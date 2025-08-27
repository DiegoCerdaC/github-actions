from typing import Annotated, Dict, List, Union
from decimal import Decimal
from utils.firebase import get_request_ctx
from .liquidity_server_api import (
    get_user_positions_in_pool_address,
    add_liquidity,
    remove_liquidity,
    claim_swap_fees,
    get_token_b_needed_amount,
    search_pools_with_user_liquidity,
)
from .meteora_dlmm import (
    get_all_pairs_by_groups,
    get_pair,
)
from utils.firebase import db_save_pool_address_for_wallet, db_get_user_open_pools
from agents.dex_agent.jupiter_functions import (
    build_jupiter_swap_transaction,
    build_jupiter_quote,
    get_jupiter_supported_token_by_symbol,
    get_jupiter_token_by_address,
)
from utils.bignumber import float_to_bignumber_string
import services.prices as prices_service
from services.prices import PriceProviderType
from utils.firebase import save_ui_message
from services.transactions import save_transaction_to_db
from services.transactions import TransactionType
from utils.firebase import save_agent_thought
from agents.unified_transfer.transfer_functions import SOL_NATIVE_ADDRESS


def get_token_price(token_address: str) -> float:
    token_price_response = prices_service.get_token_price_from_provider(
        "SOLANA", token_address, PriceProviderType.JUPITER
    )
    price = float(token_price_response["price"])
    return price


def search_for_pool(
    chat_id: Annotated[str, "The current chat id"],
    search_term: Annotated[
        str, "Search term to find pools. If nothing is specifed, use empty string."
    ],
    limit: Annotated[int, "Maximum number of results to return"] = 10,
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
) -> Annotated[
    Dict[str, Union[int, List[Dict[str, Union[str, float, int, bool]]]]],
    "Grouped pairs information. Keys: groups, total",
]:
    """
    This function searches for liquidity pools matching the search term.
    Used when the user wants to deposit but doesn't specify the pool address.
    Or when the user wants to know the available pools for a specific token pair.

    # Parameters:
    - chat_id (str): the current chat id
    - search_term (str): The search term to find pools
    - limit (int) (optional): The maximum number of results to return. By default it's 10.

    # Returns:
    - Available pools for the user to deposit into (UI component where he needs to select from)
    """
    save_agent_thought(
        chat_id=chat_id,
        thought=f"Searching for pools matching '{search_term}'...",
    )

    result = get_all_pairs_by_groups(
        search_term=search_term, limit=limit, hide_low_apr=False
    )

    if not result["groups"]:
        save_agent_thought(
            chat_id=chat_id,
            thought="No pools found matching your search criteria.",
            isFinalThought=True,
        )
        return "No pools found."

    # Cache for token prices to avoid recalculations
    cache_price_of_tokens = {}
    # List to store all valid pools before filtering
    all_valid_pools = []

    save_agent_thought(
        chat_id=chat_id,
        thought="Analyzing pool prices and liquidity...",
    )

    # The first group (is ordered by volume) has always the proper tokens (not fake ones)
    # So we can use it to skip later on the pools with not 'originals' tokens
    token_x_address = result["groups"][0]["pairs"][0]["mint_x"] or None
    token_y_address = result["groups"][0]["pairs"][0]["mint_y"] or None

    for group in result["groups"]:
        # Get mintX and mintY price (Jupiter Endpoints) - only once per group
        mint_x = group["pairs"][0]["mint_x"]
        mint_y = group["pairs"][0]["mint_y"]

        # Skip if the tokens are not the originals/verified ones
        if (
            mint_x.lower() != token_x_address.lower()
            or mint_y.lower() != token_y_address.lower()
        ):

            continue
        mintXPrice = cache_price_of_tokens.get(mint_x)
        if not mintXPrice or mintXPrice == 0:
            mintXPrice = get_token_price(mint_x)
            cache_price_of_tokens[mint_x] = mintXPrice

        mintYPrice = cache_price_of_tokens.get(mint_y)
        if not mintYPrice or mintYPrice == 0:
            mintYPrice = get_token_price(mint_y)
            cache_price_of_tokens[mint_y] = mintYPrice

        if mintXPrice == 0 or mintYPrice == 0:
            continue

        # Current Pair Price by Jupiter - calculated once per group
        currentRealPairPrice = mintXPrice / mintYPrice
        # Process all pairs in the group at once
        group_pools = []
        for pair in group["pairs"]:

            # Skip if price difference is too high
            if abs(
                float(pair["current_price"]) - currentRealPairPrice
            ) / currentRealPairPrice > Decimal(0.05):

                continue

            pool_info = {
                "address": pair.get("address", ""),
                "liquidityRate": str(pair.get("apr", "0")),
                "name": pair["name"],
                "symbol": pair["name"].split("-")[0],
                "stableBorrowRate": "",
                "totalATokenSupply": str(pair.get("reserve_x_amount", "0")),
                "totalLiquidity": str(pair.get("liquidity", "0")),
                "underlyingAsset": pair["address"],
                "currentApr": float(pair.get("apr", 0)),
                "currentApy": float(pair.get("apy", 0)),
                "logoURI": None,
                "currentPoolPrice": str(pair.get("current_price", "0")),
            }

            group_pools.append(pool_info)
        if group_pools:
            # Calculate average liquidity once per group (or totalTokenASupply if liquidity is 0 (temporary error on Meteora API))
            variable_to_filter_by = "totalLiquidity"
            if group_pools[0]["totalLiquidity"] == "0":
                variable_to_filter_by = "totalATokenSupply"

            average_liquidity_or_token_a_supply = sum(
                float(pool[variable_to_filter_by]) for pool in group_pools
            ) / len(group_pools)

            # Filter pools with sufficient Liquidity / Token A supply (above 50% of the average)
            valid_pools = [
                pool
                for pool in group_pools
                if float(pool[variable_to_filter_by])
                > average_liquidity_or_token_a_supply * 0.5
            ]

            all_valid_pools.extend(valid_pools)

    # Sort all valid pools by APY and take top 3
    all_valid_pools.sort(key=lambda x: x["currentApy"], reverse=True)
    top_pools = all_valid_pools[:3]
    if len(top_pools) == 0:
        save_agent_thought(
            chat_id=chat_id,
            thought="No valid pools found after filtering.",
            isFinalThought=True,
        )
        return "There was a problem fetching the pools. Please try again."

    if use_frontend_quoting:
        save_ui_message(
            chat_id=chat_id,
            component="meteora_pools_options",
            renderData={
                "available_pools": {"Solana": top_pools},
                "agent": "call_lp_agent",
                "protocol": "Meteora",
            },
            thought="Task completed successfully",
            isFinalThought=True,
        )
        return "Pools fetched. Please select the pool you want to deposit into from the list."
    else:
        return {"available_pools": {"Solana": top_pools}, "protocol": "Meteora"}


def get_highets_pool_by_apr(
    search_term: Annotated[
        str, "Search term to find pools. If nothing is specifed, use empty string."
    ],
    limit: Annotated[int, "Maximum number of results to return"] = 10,
):
    """
    This functions gets the highest APY pool for a specific token pair.
    Use it when the user wants to relocate their liquidity to the highest APY pool for a specific token pair.

    Args:
    - search_term (str): The search term to find pools. If nothing is specifed, use empty string.
    - limit (int) (optional): The maximum number of results to return. By default it's 10.

    Returns:
    - The address of the highest APY pool for the specific token pair.
    """
    result = get_all_pairs_by_groups(
        search_term=search_term, limit=limit, hide_low_apr=False
    )
    if not result["groups"]:
        return "No pools found."

    pairs = result["groups"][0]["pairs"]

    # Get mintX and mintY price (Jupiter Endpoints)
    mintXPrice = get_token_price(pairs[0]["mint_x"])
    mintYPrice = get_token_price(pairs[0]["mint_y"])

    currentRealPairPrice = mintXPrice / mintYPrice

    # Get Average Liquidity of Pools (without considering those with less than 50 USD of Liquidity)
    total_liquidity = 0
    total_pools = 0
    for pair in pairs:
        if Decimal(pair["liquidity"]) > Decimal(50):
            total_liquidity += Decimal(pair["liquidity"])
            total_pools += 1

    average_liquidity = total_liquidity / total_pools

    # Filter out pools that do not have at least -30% of the average liquidity
    # And those where 'current_price' differs more than 5% from the currentRealPairPrice
    pairs = [
        pair
        for pair in pairs
        if Decimal(pair["liquidity"]) > average_liquidity * Decimal(0.7)
        and abs(float(pair["current_price"]) - currentRealPairPrice)
        / currentRealPairPrice
        < Decimal(0.05)
    ]
    pairs.sort(key=lambda x: x["apr"], reverse=True)
    return pairs[0]["address"]


def display_user_positions_for_pool_term(
    chat_id: Annotated[str, "The current chat id"],
    token_a_symbol: Annotated[str, "Symbol of the first token of the pool"],
    token_b_symbol: Annotated[str, "Symbol of the second token of the pool"],
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    Fetches and displays the user's positions for a specific pool.

    Example prompts:
    - 'I want to get information about my position on SOL-USDC'
    - 'I want to know the performance of my pool MELANIA-USDC'
    - 'How did my pool USDC-TRUMP perform?'

    Args:
    - chat_id (str): The current chat id
    - token_a_symbol (str): The symbol of the first token
    - token_b_symbol (str): The symbol of the second token

    Returns:
    - str: A list of positions where the user has liquidity for information purposes
    """
    save_agent_thought(
        chat_id=chat_id,
        thought=f"Fetching positions for {token_a_symbol}-{token_b_symbol} pool...",
    )

    result = get_user_positions_for_pool_term(
        token_a_symbol=token_a_symbol,
        token_b_symbol=token_b_symbol,
        chat_id=chat_id,
        use_frontend_quoting=False,
        is_claiming_fees=False,
        is_reinvesting_fees=False,
    )

    if not result.get("positions"):
        save_agent_thought(
            chat_id=chat_id,
            thought="User doesn't have any positions in the searched pools.",
            isFinalThought=True,
        )
        return "User doesn't have any positions in the searched pools."

    if use_frontend_quoting:
        save_ui_message(
            chat_id=chat_id,
            component="meteora_pool_information",
            renderData={
                "positions": result.get("positions", []),
            },
            thought="Pool Information Successfully fetched.",
            isFinalThought=True,
        )
        return "Pool Information Successfully fetched."
    else:
        save_agent_thought(
            chat_id=chat_id,
            thought="Successfully retrieved pool information.",
            isFinalThought=True,
        )
        return {"positions": result}


def get_user_positions_for_pool_term(
    token_a_symbol: Annotated[str, "Symbol of the first token of the pool"],
    token_b_symbol: Annotated[str, "Symbol of the second token of the pool"],
    chat_id: Annotated[str, "The current chat id"],
    use_frontend_quoting: Annotated[
        bool, "If true, render UI for user to select a position"
    ] = True,
    is_claiming_fees: Annotated[
        bool,
        "If true, the user is claiming swap fees. If false, the user is withdrawing liquidity.",
    ] = True,
    is_reinvesting_fees: Annotated[
        bool, "If true, the user is reinvesting fees."
    ] = False,
):
    """
    This function retrieves the user's active positions in a specified pool.
    Call this function with the token symbols to know what pools the user has positions in when we wants to close or claim fees from them.

    Args:
    - token_a_symbol (str): The symbol of the first token
    - token_b_symbol (str): The symbol of the second token
    - chat_id (str): The current chat id
    - use_frontend_quoting (bool) (optional): Whether to render UI for user to select a position (True if the user is withrawing or claiming fees)
    - is_claiming_fees (bool) (optional): Whether the user is claiming swap fees
    - is_reinvesting_fees (bool) (optional): Whether the user is reinvesting the fees he is claiming

    # Returns:
    - str: A list of positions where the user can select one to close or claim swap fees.
    """
    save_agent_thought(
        chat_id=chat_id,
        thought="Getting user's active positions in the pool...",
    )
    solana_wallet_address = get_request_ctx(
        parentKey=chat_id, key="solana_wallet_address"
    )
    if not solana_wallet_address:
        save_agent_thought(
            chat_id=chat_id,
            thought="No wallet connected. Please connect your wallet first.",
            isFinalThought=True,
        )
        return "User doesn't have a Solana wallet address connected. Please connect your wallet first."

    if not token_a_symbol or not token_b_symbol:
        return "No token pair provided. Please provide the token pair first."

    user_active_pools = db_get_user_open_pools(solana_wallet_address, "meteora")
    if not user_active_pools:
        save_agent_thought(
            chat_id=chat_id,
            thought="No open pools found for the user.",
            isFinalThought=True,
        )
        return {
            "positions": [],
            "response_for_agent": "We couldn't find any open pools for the user. Please try again or specify yourself the pool address.",
        }

    save_agent_thought(
        chat_id=chat_id,
        thought=f"Getting {token_a_symbol} and {token_b_symbol} info...",
    )
    token_a_info = get_jupiter_supported_token_by_symbol(token_symbol=token_a_symbol)
    if token_a_info["symbol"] == "SOL" or token_a_info["symbol"] == "wSOL":
        token_a_info["address"] = SOL_NATIVE_ADDRESS

    token_b_info = get_jupiter_supported_token_by_symbol(token_symbol=token_b_symbol)

    if token_b_info["symbol"] == "SOL" or token_b_info["symbol"] == "wSOL":
        token_b_info["address"] = SOL_NATIVE_ADDRESS

    pool_list = []
    for pool_address in user_active_pools:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Getting pool info for {pool_address}...",
        )
        pool_info = get_pair(pair_address=pool_address)

        if (
            token_a_info["address"] == pool_info["mint_x"]
            and token_b_info["address"] == pool_info["mint_y"]
        ) or (
            token_a_info["address"] == pool_info["mint_y"]
            and token_b_info["address"] == pool_info["mint_x"]
        ):
            pool_list.append(
                {
                    "address": pool_address,
                    "name": pool_info["name"],
                    "apr": pool_info["apr"],
                    "apy": pool_info["apy"],
                }
            )

    save_agent_thought(
        chat_id=chat_id,
        thought="Searching for pools with user liquidity...",
    )
    positions = search_pools_with_user_liquidity(
        wallet_address=solana_wallet_address,
        pool_list=pool_list,
        is_claiming_fees=is_claiming_fees,
    )

    if not positions or len(positions) == 0:
        save_agent_thought(
            chat_id=chat_id,
            thought="No positions found in the searched pools.",
            isFinalThought=True,
        )
        return {
            "positions": [],
            "response_for_agent": "User doesn't have any positions in the searched pools.",
        }

    # Get Token Info of the first position (the tokens will be the same for all positions)
    token_a_info = get_jupiter_token_by_address(
        token_address=positions[0]["tokenXAddress"]
    )
    token_b_info = get_jupiter_token_by_address(
        token_address=positions[0]["tokenYAddress"]
    )

    save_agent_thought(
        chat_id=chat_id,
        thought="Calculating position values...",
    )

    # Pre-calculate conversion factors
    x_decimal_factor = 10 ** token_a_info["decimals"]
    y_decimal_factor = 10 ** token_b_info["decimals"]
    x_price = get_token_price(token_a_info["address"])
    y_price = get_token_price(token_b_info["address"])

    # Process all positions at once
    for pos in positions:
        x_amount = int(float(pos["tokenXAmount"])) / x_decimal_factor
        y_amount = int(float(pos["tokenYAmount"])) / y_decimal_factor
        pos.update(
            {
                "tokenXAmount": x_amount,
                "tokenYAmount": y_amount,
                "tokenXUSDAmount": x_amount * x_price,
                "tokenYUSDAmount": y_amount * y_price,
                "token_a_info": token_a_info,
                "token_b_info": token_b_info,
            }
        )

    # Sort positions by total USDAmount
    sorted_positions = sorted(
        positions,
        key=lambda pos: pos["tokenXUSDAmount"] + pos["tokenYUSDAmount"],
        reverse=True,
    )

    if use_frontend_quoting:
        save_ui_message(
            chat_id=chat_id,
            component="meteora_choose_position_to_withdraw",
            renderData={
                "positions": sorted_positions,
                "token_a_info": token_a_info,
                "token_b_info": token_b_info,
                "is_claiming_fees": is_claiming_fees,
                "is_reinvesting_fees": is_reinvesting_fees,
            },
            thought="Positions fetched successfully!",
            isFinalThought=True,
        )
        if is_claiming_fees:
            return "Please select the one you want to claim swap fees from."
        else:
            return "Please select the one you want to withdraw from."
    else:
        save_agent_thought(
            chat_id=chat_id,
            thought="Successfully retrieved position information.",
            isFinalThought=True,
        )
        return {
            "positions": sorted_positions,
            "token_a_info": token_a_info,
            "token_b_info": token_b_info,
        }


def get_user_active_positions(
    chat_id: Annotated[str, "The current chat id"],
    pool_address: Annotated[
        str, "Address of the Liquidity Pool that user has selected."
    ],
):
    """
    Gets the user's active positions in a specified pool.

    # Parameters:
    - chat_id (str): The current chat id
    - pool_address (str): The address of the liquidity pool

    # Returns:
    - The list of user's active positions in the pool
    """
    save_agent_thought(
        chat_id=chat_id,
        thought="Getting user's active positions in the pool...",
    )

    solana_wallet_address = get_request_ctx(chat_id, "solana_wallet_address")
    if not solana_wallet_address:
        return "User doesn't have a Solana wallet address connected. Please connect your wallet first."
    positions = get_user_positions_in_pool_address(
        pool_address=pool_address, wallet_address=solana_wallet_address
    )
    return positions


def deposit_liquidity(
    pool_address: Annotated[str, "Address of the Liquidity Pool"],
    token_symbol: Annotated[
        str, "Token Address/Symbol that user wants to put into the liquidity pool"
    ],
    amount: Annotated[str, "Amount user wants to deposit"],
    chat_id: Annotated[str, "The currernt chat id"],
    type: Annotated[
        str,
        "Type of Position to create. Can be 'imbalance', 'onesided','new', 'existing'. Default is 'new'",
    ] = "new",
    amountB: Annotated[
        str,
        "Amount user wants to deposit as the second token. Only apply if 'type' is 'imbalance'.",
    ] = "",
    position_address: Annotated[
        str, "Existing Position Address. Only apply if 'type' is existing."
    ] = "",
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    This function builds a transaction to deposit liquidity into a specified pool (the pool address is needed).

    # Parameters:
    - pool_address (str): The address of the liquidity pool
    - token_symbol (str): The symbol of the token to deposit
    - amount (str): The amount of the token to deposit
    - chat_id (str): The current chat id
    - type (str) (optional): The type of position to create. Can be 'imbalance', 'onesided', 'new', or 'existing'. Default is 'new'
    - amountB (str) (optional): The amount of the second token to deposit. Only apply if 'type' is 'imbalance'
    - position_address (str) (optional): The address of the existing position to deposit into. Only apply if 'type' is 'existing'

    # Returns:
    - str: The result of the task execution (quote to be confirmed by the user or error message)
    """
    try:
        solana_wallet_address = get_request_ctx(chat_id, "solana_wallet_address")
        if not solana_wallet_address:
            return "User doesn't have a Solana wallet address connected. Please connect your wallet first."

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Getting {token_symbol} info...",
        )
        token_info = get_jupiter_supported_token_by_symbol(token_symbol=token_symbol)

        if not token_info:
            return f"Token {token_symbol} not found. Please try again with a different token."

        if token_info["symbol"] == "SOL" or token_info["symbol"] == "wSOL":
            token_info["address"] = SOL_NATIVE_ADDRESS

        parsed_token_amount = int(
            Decimal(amount) * Decimal(10 ** token_info["decimals"])
        )

        # If type is not onesided, user needs to have also enough balance for the second token of the pair
        token_b_info = None
        human_readable_token_b_needed_amount = 0
        is_token_symbol_tokenX_of_pool = True
        if type != "onesided":
            token_b_needed_amount_and_address = get_token_b_needed_amount(
                pool_address=pool_address,
                token_a_amount=parsed_token_amount,
                token_a_address=token_info["address"],
            )

            token_b_info = get_jupiter_token_by_address(
                token_address=token_b_needed_amount_and_address["tokenAddress"],
            )

            if not token_b_info:
                return f"There was an error fetching quote for the pool "

            if token_b_needed_amount_and_address["isPrimaryToken"]:
                is_token_symbol_tokenX_of_pool = False

            human_readable_token_b_needed_amount = Decimal(
                token_b_needed_amount_and_address["amount"]
            ) / Decimal(10 ** token_info["decimals"])

        amount_for_add_liquidity = (
            parsed_token_amount
            if is_token_symbol_tokenX_of_pool
            else int(
                human_readable_token_b_needed_amount * 10 ** token_b_info["decimals"]
            )
        )

        save_agent_thought(
            chat_id=chat_id,
            thought="Getting pool info...",
        )

        # Construct info for display data
        pool_info = get_pair(pair_address=pool_address)
        from_token_price = get_token_price(token_info["address"])
        from_token_usd = float(amount) * float(from_token_price)
        token_b_price = get_token_price(token_b_info["address"])
        from_token_b_usd = float(human_readable_token_b_needed_amount) * float(
            token_b_price
        )
        from_token_usd += from_token_b_usd

        save_agent_thought(
            chat_id=chat_id,
            thought="Creating deposit transaction...",
        )

        add_liquidity_txn = add_liquidity(
            chat_id=chat_id,
            pool_address=pool_address,
            wallet_address=solana_wallet_address,
            amount=amount_for_add_liquidity,
            type=type,
            amountB=amountB,
            position_address=position_address,
            from_token=token_info,
            from_token_b=token_b_info,
            from_token_usd=from_token_usd,  # USD Token A + USD Token B
            pool_name=pool_info["name"],
            pool_apr=pool_info["apr"],
            pool_apy=pool_info["apy"],
            current_pool_price=pool_info["current_price"],
        )

        save_agent_thought(
            chat_id=chat_id,
            thought="Deposit transaction successfully created!",
            isFinalThought=True,
        )

        # Save pool address for user on firebase db for easier fetching of user positions later
        if use_frontend_quoting:
            db_save_pool_address_for_wallet(
                solana_wallet_address, pool_address, "meteora"
            )
            return "Successfully created quote to DEPOSIT on Meteora. Please confirm the transaction."
        else:
            return add_liquidity_txn
    except Exception as e:
        return f"Error creating quote to DEPOSIT on Meteora: {e}"


def withdraw_liquidity(
    chat_id: Annotated[str, "the current chat id"],
    pool_address: Annotated[str, "Address of the Liquidity Pool"],
    type: Annotated[
        str, "Type of withdrawal. Can be 'single'or 'all'. Default is 'all'"
    ] = "all",
    position_address: Annotated[
        str, "Existing Position Address. Only apply if 'type' is 'single'."
    ] = "",
    percentage_to_withdraw: Annotated[
        str,
        "Percentage to withdraw in numbers, example 25 / 50 / 100. 100 for withdrawing all liquidity",
    ] = 100,
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    This function constructs a withdraw liquidity transaction from a specified pool (the pool address is needed).

    # Parameters:
    - chat_id (str): the current chat id
    - pool_address (str): The address of the liquidity pool
    - type (str) (optional): The type of withdrawal. Can be 'single' or 'all'. Default is 'all'
    - position_address (str) (optional): The address of the position to withdraw from. Only apply if 'type' is 'single'
    - percentage_to_withdraw (str) (optional): The percentage of liquidity to withdraw in numbers, example 25 / 50 / 100. 100 for withdrawing all liquidity

    # Returns:
    - str: The result of the task execution (quote to be confirmed by the user or error message)
    """
    try:
        save_agent_thought(
            chat_id=chat_id,
            thought="Checking wallet connection...",
        )
        solana_wallet_address = get_request_ctx(chat_id, "solana_wallet_address")
        if not solana_wallet_address:
            save_agent_thought(
                chat_id=chat_id,
                thought="No wallet connected. Please connect your wallet first.",
                isFinalThought=True,
            )
            return "User doesn't have a Solana wallet address connected. Please connect your wallet first."

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Preparing to withdraw {percentage_to_withdraw}% of liquidity from pool {pool_address}...",
        )

        result = remove_liquidity(
            pool_address=pool_address,
            wallet_address=solana_wallet_address,
            type=type,
            position_address=position_address,
            percentage_to_withdraw=percentage_to_withdraw,
        )

        save_agent_thought(
            chat_id=chat_id,
            thought="Getting token information...",
        )

        token_a_info = get_jupiter_token_by_address(
            token_address=result.get("tokenXAddress")
        )

        token_b_info = get_jupiter_token_by_address(
            token_address=result.get("tokenYAddress")
        )

        save_agent_thought(
            chat_id=chat_id,
            thought="Calculating withdrawal amounts...",
        )

        to_token_a_amount = (
            float(result.get("totalXAmount"))
            / 10 ** token_a_info.get("decimals")
            * float(percentage_to_withdraw)
            / 100
        )
        to_token_b_amount = (
            float(result.get("totalYAmount"))
            / 10 ** token_b_info.get("decimals")
            * float(percentage_to_withdraw)
            / 100
        )

        save_agent_thought(
            chat_id=chat_id,
            thought="Getting pool information and calculating USD values...",
        )

        pool_info = get_pair(pair_address=pool_address)
        token_a_price = get_token_price(token_a_info["address"])
        token_b_price = get_token_price(token_b_info["address"])

        usd_to_withdraw = float(to_token_a_amount) * float(token_a_price) + float(
            to_token_b_amount
        ) * float(token_b_price)

        save_agent_thought(
            chat_id=chat_id,
            thought=f"You will receive approximately {to_token_a_amount:.8f} {token_a_info['symbol']} and {to_token_b_amount:.8f} {token_b_info['symbol']} (Total ≈ ${usd_to_withdraw:.2f})",
        )

        transaction_data = {
            "from_address": solana_wallet_address,
            "user_id": get_request_ctx(chat_id, "user_id"),
            "chat_id": chat_id,
            "component": "meteora_withdraw",
            "from_token": token_a_info,  # Needed for wallet-sidebar token symbol
            "to_token_a": token_a_info,
            "to_token_b": token_b_info,
            "to_token_a_amount": to_token_a_amount,
            "to_token_b_amount": to_token_b_amount,
            "to_usd_amount": usd_to_withdraw,
            "to_chain": "SOLANA",
            "to_address": solana_wallet_address,
            "pool_address": pool_address,
            "pool_name": pool_info["name"],
            "pool_apr": pool_info["apr"],
            "estimated_time": 0.5,
            "transactions": result.get("transactions"),
            "percentage_to_withdraw": float(percentage_to_withdraw),
            "from_token_usd": usd_to_withdraw,  # We use this field to track volume on main.py on "submit"
            "protocol_name": "solana",
            "transaction_type": TransactionType.WITHDRAW.value,
        }

        if use_frontend_quoting:
            save_agent_thought(
                chat_id=chat_id,
                thought="Withdrawal transaction prepared successfully. Awaiting your confirmation.",
                isFinalThought=True,
            )
            save_transaction_to_db(transaction_data)
            return "Withdraw liquidity successfully created. Please confirm the transaction."
        else:
            save_agent_thought(
                chat_id=chat_id,
                thought="Withdrawal transaction data prepared successfully.",
                isFinalThought=True,
            )
            return transaction_data
    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error creating withdrawal transaction: {str(e)}",
            isFinalThought=True,
        )
        return f"Error creating withdraw liquidity transaction: {e}"


def build_claim_swap_fees_tx(
    pool_address: Annotated[str, "Address of the Liquidity Pool"],
    chat_id: Annotated[str, "the current chat id"],
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    This function builds a transaction to claim swap fees from a liquidity pool (the pool address is needed).

    # Parameters:
    - pool_address (str): The address of the liquidity pool where the user wants to claim swap fees from
    - chat_id (str): The current chat id

    # Returns:
    - str: The result of the task execution (quote to be confirmed by the user or error message)
    """
    try:
        solana_wallet_address = get_request_ctx(chat_id, "solana_wallet_address")

        if not solana_wallet_address:
            return "User doesn't have a Solana wallet address connected. Please connect your wallet first."
        claim_swap_fee_txn = claim_swap_fees(
            pool_address=pool_address,
            wallet_address=solana_wallet_address,
            chat_id=chat_id,
        )

        if use_frontend_quoting:
            return "Claim Swap Fees Transaction successfully created. Please confirm the transaction."
        else:
            return claim_swap_fee_txn
    except Exception as e:
        return f"Error creating claim swap fees transaction: {e}"


def relocate_user_liquidity_to_highest_apy_pool(
    chat_id: str,
    token_a_symbol: str,
    token_b_symbol: str,
    amount_to_deposit: int = 0,
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
) -> str:
    """
    Builds a transaction to relocate the user's liquidity to the highest APY pool.

    # Parameters:
    - chat_id (str): the current chat id
    - token_a_symbol (str): The symbol of the first token
    - token_b_symbol (str): The symbol of the second token
    - amount_to_deposit (int) (optional): The amount of the token to deposit. If not specified, it will be 0.

    # Returns:
    - str: The result of the task execution (quote to be confirmed by the user or error message)
    """
    try:
        solana_wallet_address = get_request_ctx(chat_id, "solana_wallet_address")
        if not solana_wallet_address:
            return "User doesn't have a Solana wallet address connected. Please connect your wallet first."

        transactions = []
        token_a_withdrawn_amount = 0
        token_b_withdrawn_amount = 0
        swap_quote = None

        # Get Tokens Info
        token_a_info = get_jupiter_supported_token_by_symbol(token_a_symbol)
        token_b_info = get_jupiter_supported_token_by_symbol(token_b_symbol)

        if not token_a_info:
            return f"Token {token_a_symbol} not found. Please try again with a different token."

        if not token_b_info:
            return f"Token {token_b_symbol} not found. Please try again with a different token."

        # Update address if symbol is SOL
        if token_a_info["symbol"] == "SOL" or token_a_info["symbol"] == "wSOL":
            token_a_info["address"] = SOL_NATIVE_ADDRESS
        if token_b_info["symbol"] == "SOL" or token_b_info["symbol"] == "wSOL":
            token_b_info["address"] = SOL_NATIVE_ADDRESS

        # Get the highest APR pool for the given token pair and pool information
        highest_apy_pool_address = get_highets_pool_by_apr(
            f"{token_a_symbol}-{token_b_symbol}"
        )

        to_pool_info = get_pair(pair_address=highest_apy_pool_address)

        # If mintX is not token_a_symbol, then invert the tokens
        token_a_info["priceUSD"] = get_token_price(token_a_info["address"])
        token_b_info["priceUSD"] = get_token_price(token_b_info["address"])

        if to_pool_info["mint_x"] != token_a_info["address"]:
            # Convert amount of token with the prices
            amount_to_deposit = (
                float(amount_to_deposit)
                * float(token_a_info["priceUSD"])
                / float(token_b_info["priceUSD"])
            )

            token_a_symbol, token_b_symbol = token_b_symbol, token_a_symbol
            token_a_info, token_b_info = token_b_info, token_a_info

        user_active_pools = get_user_positions_for_pool_term(
            token_a_symbol, token_b_symbol, chat_id, use_frontend_quoting, False, False
        )

        # Construct a withdraw liquidity transaction first
        if user_active_pools["positions"]:
            # Get Pool to Withdraw From (the one with highets volume not equal to the highest_apy_pool_address)
            pool_to_withdraw = None
            for pool in user_active_pools["positions"]:
                if pool["address"] != highest_apy_pool_address:
                    pool_to_withdraw = pool
                    break

            if not pool_to_withdraw:
                return f"User already has a position in the highest APR pool for {token_a_symbol}-{token_b_symbol}. No action needed."

            from_pool_info = get_pair(pair_address=pool_to_withdraw["address"])
            from_pool_apr = from_pool_info["apr"]
            # Construct withdraw liquidity params
            withdraw_tx = remove_liquidity(
                pool_address=pool_to_withdraw["address"],
                wallet_address=solana_wallet_address,
                type="all",
                position_address="",
                percentage_to_withdraw="100",
            )

            for tx in withdraw_tx.get("transactions", []):
                transactions.append(tx)

            token_a_withdrawn_amount = float(
                withdraw_tx.get("totalXAmount")
            ) / 10 ** token_a_info.get("decimals")

            token_b_withdrawn_amount = float(
                withdraw_tx.get("totalYAmount")
            ) / 10 ** token_b_info.get("decimals")

            # If token_a and token_b withdrawn amounts are not balanced (comparing USD values), we will need to construct a swap tx to have 50% of each token
            token_b_usd_withdrawn_amount = float(token_b_withdrawn_amount) * float(
                token_b_info["priceUSD"]
            )
            token_a_usd_withdrawn_amount = float(token_a_withdrawn_amount) * float(
                token_a_info["priceUSD"]
            )

            total_usd_withdrawn = (
                token_a_usd_withdrawn_amount + token_b_usd_withdrawn_amount
            )

            token_a_proportion = token_a_usd_withdrawn_amount / total_usd_withdrawn

            if float(0.47) > token_a_proportion or token_a_proportion > float(0.53):
                token_to_swap_from = (
                    token_a_info if token_a_proportion > 0.5 else token_b_info
                )
                token_to_swap_to = (
                    token_b_info if token_a_proportion > 0.5 else token_a_info
                )

                amount_to_swap_in_usd = abs(
                    (float(0.5) * float(total_usd_withdrawn))
                    - (
                        token_a_usd_withdrawn_amount
                        if token_a_proportion > 0.5
                        else token_b_usd_withdrawn_amount
                    )
                )
                token_amount_to_swap = amount_to_swap_in_usd / float(
                    token_to_swap_from.get("priceUSD")
                )

                # Swap Tokens - Quote and then Transaction with Jupiter
                parsed_swap_amount = float_to_bignumber_string(
                    token_amount_to_swap,
                    token_to_swap_from["decimals"],
                )

                swap_quote = build_jupiter_quote(
                    input_token_address=token_to_swap_from["address"],
                    output_token_address=token_to_swap_to["address"],
                    parsed_amount=parsed_swap_amount,
                    slippage=100,
                    swap_mode="ExactIn",
                    dexes="",
                )
                swap_transaction_response = build_jupiter_swap_transaction(
                    swap_quote, solana_wallet_address
                )

                transactions.append(
                    {
                        "serializedTransaction": swap_transaction_response.json()[
                            "swapTransaction"
                        ]
                    }
                )

        if token_a_withdrawn_amount > 0:
            # In this case we will deposit half of the total USD withdrawn because there was already a pool with liquidity and we withdraw from there
            amount_to_deposit = (
                float(total_usd_withdrawn) * 0.5 / float(token_a_info["priceUSD"])
            )
        else:
            # This should be the case of the first deposit
            amount_to_deposit = float(amount_to_deposit)

        parsed_token_to_deposit = int(
            amount_to_deposit * 10 ** token_a_info.get("decimals")
        )

        token_b_needed_amount_and_address = get_token_b_needed_amount(
            pool_address=highest_apy_pool_address,
            token_a_amount=parsed_token_to_deposit,
            token_a_address=token_a_info["address"],
        )
        human_readable_token_b_needed_amount = float(
            Decimal(token_b_needed_amount_and_address["amount"])
            / Decimal(10 ** token_a_info["decimals"])
        )

        deposit_tx = add_liquidity(
            pool_address=highest_apy_pool_address,
            wallet_address=solana_wallet_address,
            amount=parsed_token_to_deposit,
            type="new",
            amountB="",
            position_address="",
            is_relocating=True,  # Flag not to render the deposit component, it is just a step on the relocate process
        )

        transactions.append({"serializedTransaction": deposit_tx["transaction"]})

        db_save_pool_address_for_wallet(
            solana_wallet_address, highest_apy_pool_address, "meteora"
        )

        from_usd_amount = float(token_a_info["priceUSD"]) * float(
            amount_to_deposit
        ) + float(token_b_info["priceUSD"]) * float(
            human_readable_token_b_needed_amount
        )

        if token_a_withdrawn_amount > 0 or token_b_withdrawn_amount > 0:
            transaction_data = {
                "chat_id": chat_id,
                "component": "meteora_relocate_liquidity",
                "from_token": token_a_info,  # Needed for wallet-sidebar token symbol
                "from_token_a": token_a_info,
                "from_token_b": token_b_info,
                "from_token_a_amount": float(token_a_withdrawn_amount),
                "from_token_b_amount": float(token_b_withdrawn_amount),
                "to_token_a_amount": float(amount_to_deposit),
                "to_token_b_amount": float(human_readable_token_b_needed_amount),
                "from_pool_address": pool_to_withdraw["address"],
                "to_pool_address": highest_apy_pool_address,
                "from_pool_name": from_pool_info["name"],
                "to_pool_name": to_pool_info["name"],
                "from_pool_apr": from_pool_apr,
                "to_pool_apr": to_pool_info["apr"],
                "from_chain": "SOLANA",
                "from_address": solana_wallet_address,
                "to_address": solana_wallet_address,
                "estimated_time": 0.5,
                "transactions": transactions,
                "closed_pool_address": pool_to_withdraw["address"],
                "from_token_usd": total_usd_withdrawn,
                "protocol_name": "solana",
                "transaction_type": TransactionType.DEPOSIT.value,
            }

            if use_frontend_quoting:
                save_transaction_to_db(transaction_data)
                return (
                    "Transactions successfully created. Please confirm the transaction."
                )
            else:
                return transaction_data
        else:
            transaction_data = {
                "chat_id": chat_id,
                "component": "meteora_deposit",
                "from_token": token_a_info,
                "from_token_b": token_b_info,
                "from_token_usd": from_usd_amount,  # USD Token A + USD Token B
                "from_amount": float(amount_to_deposit),
                "from_token_b_amount": str(human_readable_token_b_needed_amount),
                "from_chain": "SOLANA",
                "from_address": solana_wallet_address,
                "pool_address": highest_apy_pool_address,
                "pool_name": to_pool_info["name"],
                "pool_apr": to_pool_info["apr"],
                "pool_apy": to_pool_info["apy"],
                "current_pool_price": to_pool_info["current_price"],
                "estimated_time": 0.5,
                "transactions": transactions,
                "protocol_name": "solana",
                "transaction_type": TransactionType.DEPOSIT.value,
            }

            if use_frontend_quoting:
                save_transaction_to_db(transaction_data)
                return (
                    "Transactions successfully created. Please confirm the transaction."
                )
            else:
                return transaction_data
    except Exception as e:
        return f"Error creating transactions: {e}"


def claim_fees_and_reinvest(
    pool_address: str,
    chat_id: str,
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
) -> str:
    """
    This function builds a transaction to claim fees from a liquidity pool and reinvest them into the same pool.

    # Parameters:
    - pool_address (str): The address of the liquidity pool
    - chat_id (str): The current chat id

    # Returns:
    - str: The result of the task execution
    """
    try:
        solana_wallet_address = get_request_ctx(chat_id, "solana_wallet_address")
        if not solana_wallet_address:
            return "User doesn't have a Solana wallet address connected. Please connect your wallet first."

        transactions = []
        token_a_withdrawn_amount = 0
        token_b_withdrawn_amount = 0
        swap_quote = None

        to_pool_info = get_pair(pair_address=pool_address)
        token_a_address = to_pool_info["mint_x"]
        token_b_address = to_pool_info["mint_y"]

        # Get Tokens Info
        token_a_info = get_jupiter_token_by_address(token_address=token_a_address)
        token_b_info = get_jupiter_token_by_address(token_address=token_b_address)

        if not token_a_info:
            return f"Token {token_a_symbol} not found. Please try again with a different token."

        if not token_b_info:
            return f"Token {token_b_symbol} not found. Please try again with a different token."

        token_a_info["priceUSD"] = get_token_price(token_a_info["address"])
        token_b_info["priceUSD"] = get_token_price(token_b_info["address"])

        # Update address if symbol is SOL
        if token_a_info["symbol"] == "SOL" or token_a_info["symbol"] == "wSOL":
            token_a_info["address"] = SOL_NATIVE_ADDRESS
        if token_b_info["symbol"] == "SOL" or token_b_info["symbol"] == "wSOL":
            token_b_info["address"] = SOL_NATIVE_ADDRESS

        token_a_symbol = token_a_info["symbol"]
        token_b_symbol = token_b_info["symbol"]

        user_active_pools = get_user_positions_for_pool_term(
            token_a_symbol, token_b_symbol, chat_id, False, True, True
        )

        # Construct a claim fees transaction first
        if user_active_pools["positions"]:
            # Get Pool to Claim Fees
            pool_to_claim_from = None
            for pool in user_active_pools["positions"]:
                if pool["address"] == pool_address:
                    pool_to_claim_from = pool
                    break

            if not pool_to_claim_from:
                return f"You don't have a position in the pool {pool_address}."

            from_pool_info = get_pair(pair_address=pool_to_claim_from["address"])
            from_pool_apr = from_pool_info["apr"]
            from_pool_apy = from_pool_info["apy"]
            # Construct Claim Fees Transaction
            user_positions = get_user_active_positions(
                chat_id=chat_id,
                pool_address=pool_to_claim_from["address"],
            )

            position_data = user_positions.get("positions", [])[0]
            position_address = position_data.get("publicKey", "")

            claim_fees_tx = remove_liquidity(
                pool_address=pool_to_claim_from["address"],
                wallet_address=solana_wallet_address,
                type="single",
                position_address=position_address,
                percentage_to_withdraw="100",
            )

            for tx in claim_fees_tx.get("transactions", []):
                transactions.append(tx)

            token_a_withdrawn_amount = float(
                claim_fees_tx.get("totalXAmount")
            ) / 10 ** token_a_info.get("decimals")

            token_b_withdrawn_amount = float(
                claim_fees_tx.get("totalYAmount")
            ) / 10 ** token_b_info.get("decimals")

            token_a_usd_withdrawn_amount = float(token_a_withdrawn_amount) * float(
                token_a_info.get("priceUSD")
            )

            token_b_usd_withdrawn_amount = float(token_b_withdrawn_amount) * float(
                token_b_info.get("priceUSD")
            )
            total_usd_withdrawn = (
                token_a_usd_withdrawn_amount + token_b_usd_withdrawn_amount
            )

            token_a_proportion = token_a_usd_withdrawn_amount / total_usd_withdrawn

            if float(0.47) > token_a_proportion or token_a_proportion > float(0.53):
                token_to_swap_from = (
                    token_a_info if token_a_proportion > 0.5 else token_b_info
                )
                token_to_swap_to = (
                    token_b_info if token_a_proportion > 0.5 else token_a_info
                )

                amount_to_swap_in_usd = abs(
                    (float(0.5) * float(total_usd_withdrawn))
                    - (
                        token_a_usd_withdrawn_amount
                        if token_a_proportion > 0.5
                        else token_b_usd_withdrawn_amount
                    )
                )
                token_amount_to_swap = amount_to_swap_in_usd / float(
                    token_to_swap_from.get("priceUSD")
                )

                # Swap Tokens - Quote and then Transaction with Jupiter
                parsed_swap_amount = float_to_bignumber_string(
                    token_amount_to_swap,
                    token_to_swap_from["decimals"],
                )

                swap_quote = build_jupiter_quote(
                    input_token_address=token_to_swap_from["address"],
                    output_token_address=token_to_swap_to["address"],
                    parsed_amount=parsed_swap_amount,
                    slippage=100,
                    swap_mode="ExactIn",
                    dexes="",
                )

                swap_transaction_response = build_jupiter_swap_transaction(
                    swap_quote, solana_wallet_address
                )
                transactions.append(
                    {
                        "serializedTransaction": swap_transaction_response.json()[
                            "swapTransaction"
                        ]
                    }
                )

        amount_to_deposit = (
            float(total_usd_withdrawn) * 0.5 / float(token_a_info["priceUSD"])
        )

        parsed_token_to_deposit = int(
            amount_to_deposit * 10 ** token_a_info.get("decimals")
        )

        token_b_needed_amount_and_address = get_token_b_needed_amount(
            pool_address=pool_address,
            token_a_amount=parsed_token_to_deposit,
            token_a_address=token_a_info["address"],
        )

        human_readable_token_b_needed_amount = float(
            Decimal(token_b_needed_amount_and_address["amount"])
            / Decimal(10 ** token_a_info["decimals"])
        )

        deposit_tx = add_liquidity(
            chat_id=chat_id,
            pool_address=pool_address,
            wallet_address=solana_wallet_address,
            amount=parsed_token_to_deposit,
            type="new",
            amountB="",
            position_address="",
            is_relocating=True,  # Flag not to render the deposit component, it is just a step on the relocate process
        )

        transactions.append({"serializedTransaction": deposit_tx["transaction"]})

        # Balance to check calcs
        # if there is a swap, check the output token has at least the needed amount
        if swap_quote:
            if token_to_swap_from["address"] == token_a_info["address"]:
                token_to_check_balance = token_b_symbol
                token_to_check_balance_address = token_b_info["address"]
                expected_amount_to_check = human_readable_token_b_needed_amount
            else:
                token_to_check_balance = token_a_symbol
                token_to_check_balance_address = token_a_info["address"]
                expected_amount_to_check = amount_to_deposit
        else:
            token_to_check_balance = token_a_symbol
            token_to_check_balance_address = token_a_info["address"]
            expected_amount_to_check = amount_to_deposit

        transaction_data = {
            "chat_id": chat_id,
            "component": "meteora_relocate_liquidity",
            "from_token": token_a_info,  # Needed for wallet-sidebar token symbol
            "from_token_a": token_a_info,
            "from_token_b": token_b_info,
            "from_token_a_amount": float(token_a_withdrawn_amount),
            "from_token_b_amount": float(token_b_withdrawn_amount),
            "to_token_a_amount": float(amount_to_deposit),
            "to_token_b_amount": float(human_readable_token_b_needed_amount),
            "from_pool_address": pool_to_claim_from["address"],
            "to_pool_address": pool_address,
            "from_pool_name": from_pool_info["name"],
            "to_pool_name": to_pool_info["name"],
            "from_pool_apr": from_pool_apr,
            "to_pool_apr": to_pool_info["apr"],
            "from_pool_apy": from_pool_apy,
            "to_pool_apy": to_pool_info["apy"],
            "from_chain": "SOLANA",
            "from_address": solana_wallet_address,
            "to_address": solana_wallet_address,
            "estimated_time": 0.5,
            "transactions": transactions,
            "closed_pool_address": None,
            "from_token_usd": total_usd_withdrawn,
            "is_reinvesting_fees_in_same_pool": True,
            "wait_for_balance_chain": "SOLANA",
            "token_to_check": token_to_check_balance,
            "token_address_to_check": token_to_check_balance_address,
            "expected_amount_to_check": float(expected_amount_to_check),
            "wallet_to_check": solana_wallet_address,
            "protocol_name": "solana",
            "transaction_type": TransactionType.DEPOSIT.value,
        }

        if use_frontend_quoting:
            save_transaction_to_db(transaction_data)
            return "Transactions successfully created. Please confirm the transaction."
        else:
            return transaction_data
    except Exception as e:
        return f"Error creating claim and reinvest fees transactions: {e}"


def get_all_active_positions_on_meteora(
    chat_id: Annotated[str, "The current chat id"],
    use_frontend_quoting: Annotated[
        bool, "If true, render UI for user to select a position"
    ] = True,
):
    """
    This function retrieves all user's active positions in Meteora pools.
    It returns all positions where the user has liquidity, regardless of the token pair.

    Args:
    - chat_id (str): The current chat id
    - use_frontend_quoting (bool) (optional): Whether to render UI or not (mcp server)

    Returns:
    - dict: A dictionary containing all positions where the user has liquidity, sorted by total USD value

    Example prompts to use this function:
    - "I want to see all my active pools on Meteora"
    - "Show me all my active LP positions on Meteora"
    - "What active pools do I have on Meteora?"
    - "What LP positions do I have open on Meteora?"

    """
    save_agent_thought(
        chat_id=chat_id,
        thought="Getting user's active positions in Meteora pools...",
    )
    solana_wallet_address = get_request_ctx(
        parentKey=chat_id, key="solana_wallet_address"
    )
    if not solana_wallet_address:
        return "User doesn't have a Solana wallet address connected. Please connect your wallet first."

    user_active_pools = db_get_user_open_pools(solana_wallet_address, "meteora")
    if not user_active_pools:
        return {
            "positions": [],
            "response_for_agent": "We couldn't find any open pools for the user.",
        }

    pool_list = []
    for pool_address in user_active_pools:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Getting pool info for {pool_address}...",
        )
        pool_info = get_pair(pair_address=pool_address)
        pool_list.append(
            {
                "address": pool_address,
                "name": pool_info["name"],
                "apr": pool_info["apr"],
                "apy": pool_info["apy"],
            }
        )
    save_agent_thought(
        chat_id=chat_id,
        thought="Searching for pools with user liquidity...",
    )
    positions = search_pools_with_user_liquidity(
        wallet_address=solana_wallet_address,
        pool_list=pool_list,
        is_claiming_fees=False,
    )
    if not positions or len(positions) == 0:
        return {
            "positions": [],
            "response_for_agent": "User doesn't have any positions in Meteora pools.",
        }

    save_agent_thought(
        chat_id=chat_id,
        thought="Calculating position values...",
    )

    # Process all positions at once
    for pos in positions:
        # Get token info for each position using mintX and mintY
        token_a_info = get_jupiter_token_by_address(token_address=pos["tokenXAddress"])
        token_b_info = get_jupiter_token_by_address(token_address=pos["tokenYAddress"])

        # Pre-calculate conversion factors
        x_decimal_factor = 10 ** token_a_info["decimals"]
        y_decimal_factor = 10 ** token_b_info["decimals"]
        x_price = get_token_price(token_a_info["address"])
        y_price = get_token_price(token_b_info["address"])

        x_amount = int(float(pos["tokenXAmount"])) / x_decimal_factor
        y_amount = int(float(pos["tokenYAmount"])) / y_decimal_factor

        pos.update(
            {
                "tokenXAmount": x_amount,
                "tokenYAmount": y_amount,
                "tokenXUSDAmount": x_amount * x_price,
                "tokenYUSDAmount": y_amount * y_price,
                "token_a_info": token_a_info,
                "token_b_info": token_b_info,
            }
        )

    # Sort positions by total USDAmount
    sorted_positions = sorted(
        positions,
        key=lambda pos: pos["tokenXUSDAmount"] + pos["tokenYUSDAmount"],
        reverse=True,
    )
    if use_frontend_quoting:
        save_ui_message(
            chat_id=chat_id,
            component="meteora_pool_information",
            renderData={
                "positions": sorted_positions,
            },
            thought="All positions fetched successfully!",
            isFinalThought=True,
        )
        return "Please select the position you want to manage."
    else:
        return {
            "positions": sorted_positions,
        }
