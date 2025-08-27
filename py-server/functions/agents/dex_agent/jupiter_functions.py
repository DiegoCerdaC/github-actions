import traceback
from typing import Annotated, Optional
import requests
from requests.exceptions import RequestException
from utils.firebase import get_request_ctx
import services.prices as prices_service
from services.prices import PriceProviderType
from utils.firebase import save_ui_message
from services.tokens import tokens_service
from config import FIREBASE_SERVER_ENDPOINT
from utils.firebase import save_agent_thought
from agents.unified_transfer.transfer_functions import SOL_USDC_ADDRESS


# used in memecoin trader, conservative, jupiter agent, solana stake
def jupiter_get_quotes(
    input_token: Annotated[str, "Input token address/symbol"],
    output_token: Annotated[str, "Output token address/symbol"],
    amount: Annotated[float, "Input amount"],
    is_usd: Annotated[bool, "True if amount is in USD or $1, not USDC"],
    chat_id: Annotated[str, "The current chat id"],
    transaction_type: Annotated[Optional[str], "swap/stake/unstake"] = "swap",
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
) -> str:
    """Gets best swap routes sorted by output amount
    Args:
        input_token: Input token address/symbol
        output_token: Output token address/symbol
        amount: Input amount
        is_usd: True if amount is in USD
        chat_id: the current chat id
        transaction_type: swap/stake/unstake
    Returns:
        Swap quote or serialized transaction

    Swap prompt examples:
        - Swap 1 SOL to GRIFT on solana
        - Swap 1 USDC to GRIFT on solana
        - swap $1 of SOL to USDC on SOLANA
        - swap 1$ of SOL to USDC on SOLANA
        - I want to change 20 USDC to USDT on SOLANA
        - Exchange 2 SOL to PEPE on SOLANA

    Stake prompt examples:
        - stake 0.5 SOL on Solana
        - stake 1 SOL on jupSol
        - stake 1 SOL at the highest APY yield on Solana
        - Unstake 0.3 mSOL that I have staked on Solana

    """

    try:
        if not amount or amount == 0:
            if transaction_type == "stake" or transaction_type == "unstake":
                return f"Please specify the amount you want to {transaction_type}"
            else:
                return "Please specify the amount you want to swap"

        save_agent_thought(
            chat_id=chat_id,
            thought=(f"Validating input and output tokens..."),
        )

        from_token_info = tokens_service.get_token_metadata(
            chain=str("SOLANA"), token=input_token
        )
        if not from_token_info:
            return f"The input token {input_token} is not supported. Try again with a different token."

        to_token_info = tokens_service.get_token_metadata(
            chain=str("SOLANA"), token=output_token
        )
        if not to_token_info:
            return f"The output token {output_token} is not supported. Try again with a different token."

        wallet_address = get_request_ctx(parentKey=chat_id, key="solana_wallet_address")
        if not wallet_address:
            return "No Solana wallet address found"
        token_amount = amount
        if is_usd:
            token_amount = get_token_amount_from_usd(
                usd_amount=amount, token_address=from_token_info["contract_address"]
            )
            # Save thought about converting USD amount
            save_agent_thought(
                chat_id=chat_id,
                thought=(f"Converting {amount} USD to {token_amount} {input_token}"),
            )

        if use_frontend_quoting:
            save_ui_message(
                chat_id=chat_id,
                component="bridge",
                renderData={
                    "from_token": from_token_info,
                    "to_token": to_token_info,
                    "from_amount": token_amount,
                    "from_chain": "SOLANA",
                    "to_chain": "SOLANA",
                    "wallet_address": wallet_address,
                    "transaction_type": transaction_type,
                },
                thought=(f"Initiated {transaction_type.capitalize()} successfully"),
                isFinalThought=True,
            )
            return f"I've initiated the quoting process for your {transaction_type}."
        else:
            url = f"{FIREBASE_SERVER_ENDPOINT}/quote"
            params = {
                "userId": get_request_ctx(parentKey=chat_id, key="user_id"),
                "chatId": chat_id,
                "protocol": "JUPITER",
                "walletAddress": wallet_address,
                "fromTokenSymbolOrAddress": from_token_info["contract_address"],
                "toTokenSymbolOrAddress": to_token_info["contract_address"],
                "fromAmount": token_amount,
                "slippage": "100",  # by default 1%, if token is GRIFT on ts-server we adjust it
                "swapMode": "ExactIn",
                "transactionType": transaction_type,
            }
            response = requests.post(url, json=params)
            response.raise_for_status()
            result = response.json()
            return result
    except requests.exceptions.HTTPError as http_err:
        error_message = response.content.decode() if response.content else str(http_err)
        return f"There was an error building the {transaction_type} quote on Solana: {error_message}"
    except Exception as e:
        traceback.print_exc()
        return (
            f"There was an error building the {transaction_type} quote on Solana: {e}"
        )


# used in solana stake
def get_jupiter_supported_tokens():
    try:
        url = "https://lite-api.jup.ag/tokens/v2/tag?query=verified"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        tokens = response.json()
        return tokens
    except RequestException as e:
        print("Error:", e)
        return None


# used in meteora, lulo
def get_jupiter_token_by_address(token_address: str):
    try:
        url = f"https://lite-api.jup.ag/tokens/v2/search?query={token_address}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list) or len(data) == 0:
            return None
        token = data[0]
        # Map v2 response to v1 format
        v1_token = {
            "address": token.get("id"),
            "name": token.get("name"),
            "symbol": token.get("symbol"),
            "decimals": token.get("decimals"),
            "logoURI": token.get("icon"),
            "tags": token.get("tags", []),
            "daily_volume": None,  # Not available in v2
            "created_at": None,  # Not available in v2
            "freeze_authority": None,  # Not available in v2
            "mint_authority": token.get("mintAuthority"),
            "permanent_delegate": None,  # Not available in v2
            "minted_at": None,  # Not available in v2
            "extensions": {
                # v2 does not provide coingeckoId directly
            },
        }
        return v1_token
    except RequestException as e:
        print("Error: ", e)
        return None


# used in memecoin trader, conservative agent, meteora, solana staking
def get_jupiter_supported_token_by_symbol(
    token_symbol: Annotated[str, "The symbol of the token to get the info from."],
    supported_tokens: Annotated[Optional[list], "The list of supported tokens."] = None,
) -> Optional[dict]:
    """
    Retrieves the token info/metadata from the Jupiter supported tokens list by the given symbol.

    # Parameters:
    - token_symbol (str): The symbol of the token to get the info from.
    - supported_tokens (list): The list of supported tokens. If not provided, it will be fetched from the Jupiter supported tokens list.

    # Returns:
    - dict: The token info/metadata.
    """
    try:
        if not supported_tokens:
            supported_tokens = get_jupiter_supported_tokens()
        if not supported_tokens:
            return None
        for token in supported_tokens:
            # Check both the raw symbol and the symbol with a "$" prefix as some tokens have it
            if token["symbol"].lower() in [
                token_symbol.lower(),
                f"${token_symbol}".lower(),
            ]:
                return token
    except RequestException as e:
        print("Error:", e)
        return "There was an error getting the token"


# used internally here
def get_token_amount_from_usd(
    usd_amount: float,
    token_address: str,
) -> float:
    """
    This functions gets the token amount from the given USD amount before generating the jupiter quote.

    # Parameters:
    - usd_amount (float): The amount of USD to convert to the token amount.
    - token_address (str): The address of the token to get the price from.

    # Returns:
    - float: The token amount.
    """
    if token_address.lower() == SOL_USDC_ADDRESS.lower():
        return usd_amount
    token_price_response = prices_service.get_token_price_from_provider(
        "SOLANA", token_address, PriceProviderType.JUPITER
    )
    price = float(token_price_response["price"])
    if price == 0:
        raise Exception(f"Error fetching token price for {token_address}")

    return usd_amount / price


# used internally here
def compare_token_price_vs_execution_price(
    token_symbol: Annotated[str, "The symbol of the token to get the price from."],
    execution_price: Annotated[
        float, "The execution price to compare the token price to."
    ],
    expect_to_be_higher: Annotated[
        Optional[bool],
        "Whether the token price should be higher than the execution price. Default is True.",
    ] = True,
):
    """
    This function compares the token price vs the execution price.
    If expect_to_be_higher is True, the token price should be higher than the execution price.
    If expect_to_be_higher is False, the token price should be lower than the execution price.
    If that condition is not met, return a message saying that the swap will not be executed because the price condition is not met.

    # Parameters:
    - token_symbol (str): The token symbol
    - execution_price (float): The execution price

    # Returns:
    - str: The message saying whether the swap will be executed or not.
    """
    token_address = get_jupiter_supported_token_by_symbol(token_symbol)["address"]
    token_price_response = prices_service.get_token_price_from_provider(
        "SOLANA", token_address, PriceProviderType.JUPITER
    )
    token_price = float(token_price_response["price"])
    if expect_to_be_higher:
        if token_price <= execution_price:
            return False
    else:
        if token_price >= execution_price:
            return False
    return True


# used in meteora
def build_jupiter_quote(
    input_token_address, output_token_address, parsed_amount, slippage, swap_mode, dexes
):
    url = f"https://lite-api.jup.ag/swap/v1/quote?inputMint={input_token_address}&outputMint={output_token_address}&amount={parsed_amount}&slippageBps={slippage}&swapMode={swap_mode}&onlyDirectRoutes=false&asLegacyTransaction=false&experimentalDexes=Jupiter%20LO{dexes if dexes else ''}"
    headers = {"Accept-Encoding": "gzip,deflate,compress"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.json()


# used in meteora
def build_jupiter_swap_transaction(swap_quote, wallet_address):
    swap_transaction_response = requests.post(
        "https://lite-api.jup.ag/swap/v1/swap",
        headers={
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip,deflate,compress",
        },
        json={
            "quoteResponse": swap_quote,
            "userPublicKey": wallet_address,
            "asLegacyTransaction": False,
            "dynamicComputeUnitLimit": True,
            "prioritizationFeeLamports": {"autoMultiplier": 2},
        },
    )
    swap_transaction_response.raise_for_status()
    return swap_transaction_response
