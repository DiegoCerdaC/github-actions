import requests
from typing import Annotated, Dict, Any
from config import LULO_API_KEY

# Utils
from utils.firebase import get_request_ctx, save_ui_message, save_agent_thought

# Services
import services.prices as prices_service
from services.prices import PriceProviderType
from services.tokens import tokens_service
from services.transactions import save_transaction_to_db
from services.transactions import TransactionType
from services.balances import get_single_token_balance

from agents.dex_agent.jupiter_functions import get_jupiter_token_by_address


if not LULO_API_KEY:
    raise ValueError("LULO_API_KEY is not set in the environment variables")

supported_protocols = [
    "marginfi",
    "kamino",
    "solend",
    "drift",
    "kamino_jlp",
    "kam_alt",
    "flexlend",
]


supported_tokens = {
    "usdc": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "pyusd": "2b1kV6DkPAnxd5ixfnxCpjxmKwqjjaYmCZfHsFu24GXo",
    "usds": "USDSwr9ApdHk5bvJKMjzff41FfuX8bSxdKcR81vTwcA",
    "usdt": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
    "fdusd": "9zNQRsGLjNKwCUU5Gq5LR8beUCPzQMVMqKAi3SSZh54u",
    "sol": "So11111111111111111111111111111111111111112",
}


token_minimum_amount_to_deposit = {
    "usdc": 1,
    "pyusd": 1,
    "usds": 1,
    "usdt": 1,
    "fdusd": 1,
    "sol": 0.5,
}

# If the user wants to deposit +50K, we need to call the route_estimate portion first
MIN_ROUTE_ESTIMATE_VALUE = 50000


def get_token_symbol_from_address(
    address: Annotated[str, "The address of the token to get the symbol for."],
) -> Annotated[str, "The symbol of the token."]:
    for symbol, addr in supported_tokens.items():
        if addr == address:
            return symbol
    return ""  # Return empty string instead of None to match return type


def is_token_supported(
    mint_address_or_symbol: Annotated[
        str, "The mint address or symbol to check if it is supported by Lulo."
    ],
) -> bool:
    """
    Check if a token is supported based on its symbol or mint address.
    # Parameter:
        mint_address_or_symbol (str): The token's symbol (e.g., 'USDT') or mint address.
    # Returns:
        bool: True if the token is supported, False otherwise.
    """
    normalized_input = mint_address_or_symbol.lower()

    normalized_tokens = {
        key.lower(): value.lower() for key, value in supported_tokens.items()
    }

    return (
        normalized_input in normalized_tokens
        or normalized_input in normalized_tokens.values()
    )


def fetch_account_info(
    wallet_pubkey: Annotated[
        str, "The public key of the wallet to fetch the account info for."
    ],
    chat_id: Annotated[str, "The current chat id"],
):
    """
    Fetch the account info for a given wallet.

    # Parameters:
    - wallet_pubkey (str): The public key of the wallet to fetch the account info for.
    - chat_id (str): The current chat id

    # Returns:
        dict: A dictionary containing the account info for the given wallet.
    Example:
        {
            "Current Orders": 0,
            "Total Value": 0,
            "Interest Earned": 0.002724 USDC,
            "Realtime APY": 0,
            "Historical APY": 0,
            "Allowed Protocols": ["drift", "kamino", "marginfi", "solend", "kamino_jlp", "kam_alt"],
        }
    """
    try:
        save_agent_thought(
            chat_id=chat_id,
            thought="Fetching your account information...",
        )
        headers = {"x-wallet-pubkey": wallet_pubkey, "x-api-key": LULO_API_KEY}
        response = requests.get("https://api.flexlend.fi/account", headers=headers)

        if response.status_code != 200:
            error_message = response.json().get("message", "Unknown error occurred")
            return f"Error fetching user account info: {error_message}. Status code: {response.status_code}"

        return response.json()
    except requests.exceptions.RequestException as e:
        return f"Network error occurred while fetching account info: {str(e)}"
    except ValueError as e:
        return f"Error parsing response from Lulo API: {str(e)}"
    except Exception as e:
        return f"Unexpected error occurred while fetching account info: {str(e)}"


def get_user_deposits(
    wallet_pubkey: Annotated[
        str, "The public key of the wallet to fetch the account info for."
    ],
    chat_id: Annotated[str, "the current chat id"],
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    Gets the current deposits of the user on Lulo - Yield Agent

    Args:
        wallet_pubkey (str): The public key of the wallet to fetch the account info for.
        chat_id (str): The current chat id
        use_frontend_quoting (bool): Whether to use frontend quoting or not.

    Returns:
        dict: A message indicating the the information was fetched successfully or that the user doesn't have any deposits.
    """

    try:
        user_account_info = fetch_account_info(wallet_pubkey, chat_id)
        if user_account_info["data"]["currentOrders"] == 0:
            save_agent_thought(
                chat_id=chat_id,
                thought="No deposits found in your account",
                isFinalThought=True,
            )
            return "You don't have any current deposits on Lulo."
        else:
            save_agent_thought(
                chat_id=chat_id,
                thought="Account information fetched successfully. Processing...",
            )

            data = user_account_info["data"]

            # Add token metadata to each token balance
            for token_balance in data["tokenBalances"]:
                mint = token_balance["mint"]
                token_info = tokens_service.get_token_metadata(
                    chain="SOLANA", token=mint
                )
                token_balance.update(token_info)

        if use_frontend_quoting:
            # Save the updated data with token metadata
            save_ui_message(
                chat_id=chat_id,
                component="lulo_user_deposits",
                renderData={**data},
                thought="Account information fetched successfully!",
                isFinalThought=True,
            )
            return "Your current deposits on Lulo were successfully fetched."
        else:
            return data
    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error fetching deposits: {str(e)}",
            isFinalThought=True,
        )
        return f"Error fetching user deposits: {e}"


def get_route_estimate(
    amount: Annotated[int, "The amount to estimate the route for."],
    mint_address: Annotated[
        str, "The mint address of the token to estimate the route for."
    ],
    owner: Annotated[str, "The owner of the token to estimate the route for."],
):
    """
    Get the route estimate for a given amount, mint address, and owner.

    # Parameters:
    - amount (int): The amount to estimate the route for.
    - mint_address (str): The mint address of the token to estimate the route for.
    - owner (str): The owner of the token to estimate the route for.

    # Returns:
    - dict: A dictionary containing the route estimate.
    """
    try:
        response = requests.get(
            "https://api.lulo.fi/v0/routing.getRouteEstimate",
            params={
                "amount": amount,
                "mintAddress": mint_address,
                "owner": owner,
            },
        )
        return response.json()
    except Exception as e:
        return "Error getting route estimate"


def is_account_created(
    wallet_pubkey: Annotated[
        str, "The public key of the wallet to check if the account is created."
    ],
):
    try:
        headers = {"x-wallet-pubkey": wallet_pubkey, "x-api-key": LULO_API_KEY}
        response = requests.get(
            "https://api.lulo.fi/v0/account.getAccount", headers=headers
        )
        response_json = response.json()
        return bool(response_json.get("accountExists", False))
    except Exception as e:
        return False


def generate_deposit_transaction(
    chat_id: Annotated[str, "The current chat id"],
    wallet_pubkey: Annotated[
        str, "The public key of the wallet to generate the deposit transaction for."
    ],
    mint_address_or_symbol: Annotated[
        str, "The address or symbol of the token to deposit."
    ] = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # If swap, USDS Address
    deposit_amount: Annotated[str, "The amount of the deposit."] = "100",
    swap_from_token: Annotated[
        str, "Symbol or address of the token to swap from"
    ] = None,
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    Generate a new deposit transaction (or transactions, if swap_from_token is provided), which the sending wallet can sign and submit.
    If a swaps is needed, returns a question for the user to choose which token to swap from.

    # Parameters:
    - chat_id (str): The current chat id
    - wallet_pubkey (str): The public key of the wallet to generate the deposit transaction for.
    - mint_address_or_symbol (str): The mint address (token address) or token symbol to deposit.
    - deposit_amount (str): The amount of the deposit.
    - swap_from_token (str) (optional): The address or symbol of the token to swap from. By default it's None.
        Do not include any swap_from_token if the user doesn't specify one.
    - use_frontend_quoting (bool) (optional): Whether to use frontend quoting or not. By default it's True.

    # Returns:
    - A message indicating whether the deposit transaction was successfully created.

    """
    try:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Initiating deposit of {deposit_amount} {mint_address_or_symbol}...",
        )

        if not deposit_amount or float(deposit_amount) == 0:
            save_agent_thought(
                chat_id=chat_id,
                thought="Deposit failed: Amount not specified",
                isFinalThought=True,
            )
            return "Please specify the amount you want to deposit"

        token_info = tokens_service.get_token_metadata(
            chain="SOLANA", token=mint_address_or_symbol
        )
        if not token_info or token_info["address"] not in supported_tokens.values():
            save_agent_thought(
                chat_id=chat_id,
                thought=f"Deposit failed: Token {token_info['symbol']} not supported",
                isFinalThought=True,
            )
            return f"Token {token_info['symbol']} not supported by Lulo"

        save_agent_thought(
            chat_id=chat_id,
            thought="Checking account status...",
        )

        if not is_account_created(wallet_pubkey):
            save_agent_thought(
                chat_id=chat_id,
                thought="Account not created, checking SOL balance for fees...",
            )
            solana_user_balance = get_single_token_balance(
                wallet_pubkey, "SOLANA", "SOL"
            )
            if float(solana_user_balance) < float(0.005):
                save_agent_thought(
                    chat_id=chat_id,
                    thought="Deposit failed: Insufficient SOL for fees",
                    isFinalThought=True,
                )
                return "Insufficient SOL balance for paying deposit fees. You need at least 0.005 SOL on your wallet."

        if not use_frontend_quoting:
            transactions = []

            # Get User Balance to check if he has enough or he needs to swap from another token
            deposit_token_balance = get_single_token_balance(
                wallet_pubkey, "SOLANA", token_info["symbol"]
            )

            from_token_price_response = prices_service.get_token_price_from_provider(
                "SOLANA", token_info["address"], PriceProviderType.JUPITER
            )
            from_token_price = float(from_token_price_response["price"])

            if (
                float(deposit_token_balance) < float(deposit_amount)
                and not swap_from_token
            ):

                # Calculate how much he needs to swap from another token
                swap_amount = float(deposit_amount) - float(deposit_token_balance)
                # Add a 5% surplus for swap fees and slippage
                swap_amount = swap_amount * 1.05

                # Amount in USD needed
                swap_amount_usd = round(swap_amount * float(from_token_price), 2)

                token_symbol = token_info["symbol"]
                return f"You don't have enough {token_symbol}. You need to swap {swap_amount_usd} USD from another token. Please specify which token you want to swap from the amount of {swap_amount_usd} dollars to {token_symbol} to make the swap and deposit. TERMINATE"

            if not is_token_supported(token_info["symbol"]):
                return f"Token {token_info['symbol']} not supported by Lulo"

            # Check min deposit amount
            minimum_amount = token_minimum_amount_to_deposit.get(
                token_info["symbol"].lower(), None
            )

            if minimum_amount is None:
                return f"Minimum deposit amount not defined for {token_info['symbol']}."

            if float(deposit_amount) < float(minimum_amount):
                difference = minimum_amount - float(deposit_amount)
                return f"Deposit amount too low. Minimum required for {token_info['symbol']} is {minimum_amount}. Please add {difference} {token_info['symbol']} to proceed."

            from_token_usd = float(deposit_amount) * float(from_token_price)
            headers = {"Content-Type": "application/json", "x-api-key": LULO_API_KEY}

            input_token_rates = find_and_render_better_rates(
                token_info["address"], supported_protocols
            )

            ################################################################
            ############ LULO V1 DEPOSITS REGION (PROTECTED) #############
            # response = requests.post(
            #     f"https://api.lulo.fi/v1/generate.transactions.deposit?priorityFee={priority_fee}",
            #     headers=headers,
            #     json={
            #         "owner": wallet_pubkey,
            #         "mintAddress": token_info["address"],
            #         "protectedAmount": float(deposit_amount),
            #     },
            # )
            # response.raise_for_status()

            # transaction = response.json()["transaction"]
            # transactions.append({"serializedTransaction": transaction})
            ################################################################
            ######################## END REGION ############################

            ################################################################
            ############# LULO V0 DEPOSITS REGION (CLASSIC) ################
            MIN_ROUTE_ESTIMATE_VALUE = 50000
            body = {
                "owner": wallet_pubkey,
                "mintAddress": token_info["address"],
                "depositAmount": float(deposit_amount),
                "skipInitFlexUser": False,  # False to automatically create the "create_account" tx for new users
            }

            if float(from_token_usd) > float(MIN_ROUTE_ESTIMATE_VALUE):
                route_estimate = get_route_estimate(
                    float(deposit_amount), token_info["address"], wallet_pubkey
                )
                body["estimateResponse"] = route_estimate

            response = requests.post(
                f"https://api.lulo.fi/v0/generate.transactions.deposit?priorityFee=100000",
                headers=headers,
                json=body,
            )
            response.raise_for_status()

            transaction = response.json()["transactionMeta"][0]["transaction"]
            transactions.append({"serializedTransaction": transaction})
            ################################################################
            ######################## END REGION ############################
            transaction_data = {
                "user_id": get_request_ctx(chat_id, "user_id"),
                "component": "yield_lulo",
                "chat_id": chat_id,
                "walletAddress": wallet_pubkey,
                "from_token": token_info,
                "from_token_usd": from_token_usd,
                "from_amount": deposit_amount,
                "from_chain": "SOLANA",
                "from_address": wallet_pubkey,
                "estimated_time": 0.01,
                "transactions": transactions,
                "protocol": "Lulo",
                "total_deposit": deposit_amount,
                "input_token_rates": (
                    input_token_rates
                    if input_token_rates
                    else "Rates not available at the moment. Please try again later."
                ),
                "transaction_type": TransactionType.DEPOSIT.value,
                "extra_note": (
                    "Sign the swap transaction first. Then this deposit quote."
                    if swap_from_token
                    else None
                ),
            }

            save_transaction_to_db(transaction_data)
            return transaction_data
        else:
            token_minimum_amount = token_minimum_amount_to_deposit.get(
                token_info["symbol"].lower(), None
            )

            if float(deposit_amount) < float(token_minimum_amount):
                difference = token_minimum_amount - float(deposit_amount)
                save_agent_thought(
                    chat_id=chat_id,
                    thought=f"Deposit failed: Amount below minimum ({token_minimum_amount} {token_info['symbol']})",
                    isFinalThought=True,
                )
                return f"Deposit amount too low. Minimum required for {token_info['symbol']} is {token_minimum_amount}. Please add {difference} {token_info['symbol']} to proceed."
            save_ui_message(
                chat_id=chat_id,
                component="yield_lulo",
                renderData={
                    "owner": wallet_pubkey,
                    "token": mint_address_or_symbol,
                    "amount": float(deposit_amount),
                    "skipInitFlexUser": False,  # False to automatically create the "create_account" tx for new users
                    "transaction_type": TransactionType.DEPOSIT.value,
                },
                thought="Task completed successfully",
                isFinalThought=True,
            )

            return "I've initiated the quoting process for your deposit."
    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error during deposit: {str(e)}",
            isFinalThought=True,
        )
        return f"Error generating deposit transaction because: {e}"


# LULO V0 CLASSIC WITHDRAWAL TRANSACTIONS
def generate_withdrawal_transaction(
    chat_id: Annotated[str, "The current chat id"],
    wallet_pubkey: Annotated[
        str, "The public key of the wallet to generate the withdrawal transaction for."
    ],
    mint_address_or_symbol: Annotated[
        str, "The address or symbol of the token to withdraw from."
    ] = "USDC",
    withdraw_amount: Annotated[str, "The amount to withdraw."] = None,
    withdraw_percentage: Annotated[
        int, "The percentage to withdraw, ranging from 0 to 100."
    ] = None,
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    Generate a new withdrawal transaction (or transactions), which the sending wallet can sign and submit.
    One of withdraw_amount or withdraw_percentage must be provided.

    # Parameters:
    - chat_id (str): The current chat id
    - wallet_pubkey (str): The public key of the wallet to generate the withdrawal transaction for.
    - mint_address_or_symbol (str): The mint address (token address) or symbol to withdraw from.
    - withdraw_amount (str) (optional): The amount to withdraw.
    - withdraw_percentage (int) (optional): The percentage to withdraw, ranging from 0 to 100.
    - use_frontend_quoting (bool) (optional): Whether to use frontend quoting or not. By default it's True.


    # Returns:
    - A message indicating whether the withdrawal transaction was successfully created.

    """
    try:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Initiating withdrawal request for {mint_address_or_symbol}...",
        )

        account_info = fetch_account_info(wallet_pubkey, chat_id)
        if not use_frontend_quoting:
            token_info = tokens_service.get_token_metadata(
                chain="SOLANA",
                token=mint_address_or_symbol,
            )
            if not is_token_supported(token_info["symbol"]):
                return f"Token {token_info['symbol']} not supported by Lulo"

            if not withdraw_amount and not withdraw_percentage:
                return "Please specify the Amount or Percentage to withdraw."

            mint_address = token_info["address"]
            try:
                if account_info["data"]["currentOrders"] == 0:
                    return "No active orders found."

                if mint_address not in [
                    balance["mint"] for balance in account_info["data"]["tokenBalances"]
                ]:
                    return f"Token not found in the account balance. {account_info['data']['tokenBalances']}"

                max_withdrawable = next(
                    (
                        item["balance"]
                        for item in account_info["data"]["tokenBalances"]
                        if item["mint"] == mint_address
                    ),
                    0,
                )

                if withdraw_percentage:
                    withdraw_amount = float(
                        max_withdrawable * withdraw_percentage / 100
                    )

                if max_withdrawable < float(withdraw_amount):
                    return f"Insufficient balance to withdraw {withdraw_amount} {token_info['symbol']}. Maximum withdrawable amount is {max_withdrawable}."

            except Exception as e:
                return f"Error accessing account info: {str(e)}"

            from_token_price_response = prices_service.get_token_price_from_provider(
                "SOLANA", token_info["address"], PriceProviderType.JUPITER
            )
            from_token_price = float(from_token_price_response["price"])
            from_token_usd = float(withdraw_amount) * float(from_token_price)

            request = {
                "owner": wallet_pubkey,
                "mintAddress": token_info["address"],
                "withdrawAmount": float(withdraw_amount),
            }
            response = requests.post(
                f"https://api.lulo.fi/v0/generate.transactions.withdraw?priorityFee=950000",
                json=request,
            )
            transaction_data = response.json()["transactionMeta"][0]
            transaction = transaction_data["transaction"]
            total_withdraw = transaction_data["totalWithdraw"]

            transactions = [{"serializedTransaction": transaction}]
            transaction_data = {
                "user_id": get_request_ctx(chat_id, "user_id"),
                "component": "yield_lulo",
                "chat_id": chat_id,
                "walletAddress": wallet_pubkey,
                "from_token": token_info,
                "from_token_usd": from_token_usd,
                "from_amount": withdraw_amount,
                "from_chain": "SOLANA",
                "from_address": wallet_pubkey,
                "estimated_time": 0.01,
                "transactions": transactions,
                "protocol": "Lulo",
                "total_withdraw": str(total_withdraw),
                "transaction_type": TransactionType.WITHDRAW.value,
            }

            save_transaction_to_db(transaction_data)
            return transaction_data
        else:
            user_deposits = (
                account_info["data"]["tokenBalances"]
                if account_info["data"]["tokenBalances"]
                else []
            )
            save_ui_message(
                chat_id=chat_id,
                component="yield_lulo",
                renderData={
                    "owner": wallet_pubkey,
                    "token": mint_address_or_symbol,
                    "amount": float(withdraw_amount) if withdraw_amount else None,
                    "percentage": withdraw_percentage if withdraw_percentage else None,
                    "transaction_type": TransactionType.WITHDRAW.value,
                    "accountDeposits": user_deposits,
                },
                thought="Task completed successfully",
                isFinalThought=True,
            )

            return "I've initiated the quoting process for your withdrawal. Please wait a moment."
    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error during withdrawal: {str(e)}",
            isFinalThought=True,
        )
        return f"Error generating withdrawal transaction: {e}"


# LULO V1 WITHDRAWAL TRANSACTIONS
# def generate_withdrawal_transaction(
#     wallet_pubkey: Annotated[
#         str, "The public key of the wallet to generate the withdrawal transaction for."
#     ],
#     mint_address_or_symbol: Annotated[
#         str, "The address or symbol of the token to withdraw from."
#     ] = "USDC",
#     withdraw_amount: Annotated[str, "The amount to withdraw."] = "100",
#     priority_fee: Annotated[
#         str,
#         "The priority fee to use for the withdrawal transaction. Priority fee is required on all generated transactions, and is specified in terms of total SOL lamports. i.e priorityFee=500_000  will add a 0.0005 SOL priority fee to the transaction",
#     ] = "950000",
# ):
#     """
#     Generate a new withdrawal transaction (or transactions), which the sending wallet can sign and submit.

#     # Parameters:
#     - wallet_pubkey (str): The public key of the wallet to generate the withdrawal transaction for.
#     - mint_address_or_symbol (str): The mint address (token address) or symbol to withdraw from.
#     - withdraw_amount (str): The amount to withdraw.
#     - priority_fee (str) (optional): The priority fee to use for the withdrawal transaction. By default it's 950000.

#     # Returns:
#     - A message indicating whether the withdrawal transaction was successfully created.

#     """
#     try:
#         token_info = tokens_service.get_token_metadata(
#             chain="SOLANA",
#             token=mint_address_or_symbol,
#         )

#         if not is_token_supported(token_info["symbol"]):
#             return "Token not supported by Lulo"

#         try:
#             response = requests.get(
#                 f"https://api.lulo.fi/v1/account.getAccount?owner={wallet_pubkey}",
#                 headers={"Content-Type": "application/json"},
#             )
#             account_data = response.json()
#             if account_data.get("totalUsdValue", 0) == 0:
#                 return "No active orders found."

#             max_withdrawable = account_data.get("maxWithdrawable", {})
#             protected_balances = max_withdrawable.get("protected", {})
#             regular_balances = max_withdrawable.get("regular", {})

#             if (
#                 token_info["address"] not in protected_balances
#                 and token_info["address"] not in regular_balances
#             ):
#                 return f"Token not found in the account balance."
#         except Exception as e:
#             return f"Error accessing account info: {str(e)}"

#         from_token_price_response = prices_service.get_token_price_from_provider(
#             "SOLANA", token_info["address"], PriceProviderType.JUPITER
#         )
#         from_token_price = float(from_token_price_response["price"])
#         from_token_usd = float(withdraw_amount) * float(from_token_price)

#         headers = {
#             "Content-Type": "application/json",
#             "x-wallet-pubkey": wallet_pubkey,
#             "x-api-key": LULO_API_KEY,
#         }

#         request = {
#             "owner": wallet_pubkey,
#             "mintAddress": token_info["address"],
#             "amount": float(withdraw_amount),
#         }
#         response = requests.post(
#             f"https://api.lulo.fi/v1/generate.transactions.withdrawProtected?priorityFee={priority_fee}",
#             headers=headers,
#             json=request,
#         )

#         transaction = response.json()["transaction"]

#         transactions = [{"serializedTransaction": transaction}]
#         transaction_data = {
#             "user_id": get_request_ctx("user_id"),
#             "component": "yield_lulo",
#             "chat_id": get_request_ctx("session_id"),
#             "walletAddress": wallet_pubkey,
#             "from_token": token_info,
#             "from_token_usd": from_token_usd,
#             "from_amount": withdraw_amount,
#             "from_chain": "SOLANA",
#             "from_address": wallet_pubkey,
#             "estimated_time": 0.01,
#             "transactions": transactions,
#             "protocol": "Lulo",
#             "total_withdraw": withdraw_amount,
#         }

#         save_transaction_to_db(transaction_data)

#         return "Successfully created quote to WITHDRAW on Lulo. Please confirm the transaction."
#     except Exception as e:
#         return f"Error generating withdrawal transaction: {e}"


def fetch_protocol_rates_raw() -> Dict[str, Any]:
    try:
        url = "https://api.lulo.fi/v0/pools.getPoolMeta"
        response = requests.get(url)
        response.raise_for_status()  # Lanza excepción si hay error HTTP
        yields_pools_information = response.json()
        formatted_rates = format_protocol_rates(yields_pools_information)
        return formatted_rates
    except Exception as error:
        print(f"Error occurred: {error}")
        return {}


def format_protocol_rates(yield_pools_information):
    formatted_rates = []
    for token_address, protocol_rates in yield_pools_information["rates"].items():
        token_info = get_jupiter_token_by_address(token_address)
        if not token_info:
            continue

        for timeframe, protocols in protocol_rates.items():
            for protocol, rate in protocols.items():
                protocol_data = next(
                    (p for p in formatted_rates if p["protocol"] == protocol), None
                )
                if not protocol_data:
                    protocol_data = {"protocol": protocol, "rates": {}}
                    formatted_rates.append(protocol_data)

                token_minimum_amount = token_minimum_amount_to_deposit.get(
                    token_info["symbol"].lower(), 0
                )

                if token_address not in protocol_data["rates"]:
                    protocol_data["rates"][token_address] = {
                        "address": token_info["address"],
                        "logoURI": token_info["logoURI"],
                        "name": token_info["name"],
                        "symbol": token_info["symbol"],
                        "decimals": token_info["decimals"],
                        "token_minimum_amount": token_minimum_amount,
                    }

                token_rates = protocol_data["rates"][token_address]
                if timeframe == "CURRENT":
                    token_rates["CURRENT"] = str(rate)
                elif timeframe == "1HR":
                    token_rates["1HR"] = str(rate)
                elif timeframe == "24HR":
                    token_rates["24HR"] = str(rate)
                elif timeframe == "7DAY":
                    token_rates["7DAY"] = str(rate)
                elif timeframe == "30DAY":
                    token_rates["30DAY"] = str(rate)

    return formatted_rates


def find_and_render_better_rates(
    mint_address: Annotated[str, "The address of the token to find better rates for."],
    allowed_protocols: Annotated[
        list,
        "The allowed protocols from the user's account info to find better rates for.",
    ],
) -> Annotated[
    float,
    "The rate of the input token to be used in the deposit transaction.",
]:
    """
    Find better APR alternatives for a given token within allowed protocols.
    Also renders the UI for the better rates directly to the user.
    Returns the rate of the input token to be used in the deposit transaction.

    Args:
        mint_address (str): The token address to compare against
        allowed_protocols (list): List of allowed protocol names from the user's account info

    Returns:
        float: The rate of the input token to be used in the deposit transaction.
    """
    try:
        protocols = fetch_protocol_rates_raw()  # Fetch raw data
        input_token_rates = []

        for protocol_data in protocols:
            if protocol_data["protocol"] not in allowed_protocols:
                continue

            rates = protocol_data["rates"]
            if mint_address in rates:
                input_token_rates = {
                    "CURRENT": float(rates[mint_address].get("CURRENT", 0)),
                    "1HR": float(rates[mint_address].get("1HR", 0)),
                    "24HR": float(rates[mint_address].get("24HR", 0)),
                    "30DAY": float(rates[mint_address].get("30DAY", 0)),
                    "7DAY": float(rates[mint_address].get("7DAY", 0)),
                }
                break

        return input_token_rates
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_stable_coin_rates():
    protocols = fetch_protocol_rates_raw()  # Fetch raw data

    # Filter only stable tokens marked with #
    stable_tokens = {
        k: v
        for k, v in supported_tokens.items()
        if k in ["usdc", "pyusd", "usds", "usdt", "fdusd"]
    }

    stable_coin_rates = {}
    for protocol in protocols:
        for token_address, rate_info in protocol["rates"].items():
            if token_address in stable_tokens.values():
                if protocol["protocol"] not in stable_coin_rates:
                    stable_coin_rates[protocol["protocol"]] = {}
                stable_coin_rates[protocol["protocol"]][token_address] = rate_info

    return stable_coin_rates
