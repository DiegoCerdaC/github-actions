import requests
from typing_extensions import Annotated
from decimal import Decimal

# utils
from utils.firebase import get_request_ctx, save_ui_message, save_agent_thought
from config import FIREBASE_SERVER_ENDPOINT

# services
import services.prices as prices_service
from services.chains import call_chains_service
from services.prices import PriceProviderType
from services.tokens import tokens_service
from services.transactions import TransactionType

# used internally and in action card
supported_chains = [
    "POLYGON",
    "ETHEREUM",
    "BINANCE",
    "AVALANCHE",
    "OPTIMISM",
    "ARBITRUM",
    "BASE",
    "LINEA",
    "MODE",
    "ZKSYNC",
    "SOLANA",
    "BLAST",
    "SCROLL",
    "POLYGONZKEVM",
    "GNOSIS",
    "FANTOM",
    "MOONRIVER",
    "MOONBEAM",
    "FUSE",
    "BOBA",
    "METIS",
    "AURORA",
    "MANTLE",
    "CELO",
    "EVMOS",
    "SEI",
    "IMMUTABLEZKEVM",
    "FRAXTAL",
    "TAIKO",
    "GRAVITY",
    "ROOTSTOCK",
    "BITCOIN",
    "CRONOS",
    "WORLD CHAIN",
]


# used internally
def supports_bridge(
    chain: str,
) -> bool:
    return chain.upper() in supported_chains


def lifi_get_quote(
    from_chain: Annotated[str, "The name of the origin chain"],
    to_chain: Annotated[str, "The name of the destination chain"],
    from_token_symbol: Annotated[str, "The symbol of the origin token"],
    to_token_symbol: Annotated[str, "The symbol of the destination token"],
    from_amount: Annotated[str, "The amount of tokens to bridge in a float format"],
    is_usd: Annotated[
        bool,
        "Should only be true if from_amount is like (only for $ inputs or like 1 USD). Otherwise, it is false.",
    ],
    chat_id: Annotated[str, "The current chat id"],
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    This function gets a quote for a cross-chain swap or bridge transaction using the LiFi protocol.
    It's used for swaps on EVM chains, bridges on EVM↔EVM, Solana↔EVM or EVM↔Solana.

    # Parameters:
    - from_chain (str): The name of the origin chain. DO NOT MODIFY CHAIN IF PROVIDED.
    - to_chain (str): The name of the destination chain. DO NOT MODIFY CHAIN IF PROVIDED.
    - from_token_symbol (str): The symbol of the origin token. DO NOT MODIFY TOKEN SYMBOL OR ADDRESS IF PROVIDED.
    - to_token_symbol (str): The symbol of the destination token. DO NOT MODIFY TOKEN SYMBOL OR ADDRESS IF PROVIDED.
    - from_amount (str): The amount of tokens to bridge in a float format
    - is_usd (bool): Should only be true if from_amount is like (only for $ inputs or like 1 USD). Otherwise, it is false.
    - chat_id (str): the current chat id

    # Returns:
    - str: Message indicating the quote was created successfully or an error message if there was an issue

    # Prompt examples:
        Swaps (same chain):
        - Swap 100 USDC to USDT on Ethereum
        - Swap $1 of USDC to USDT on Polygon
        - Exchange 3 AVAX to USDC on Avalanche
        Bridges (cross-chain):
        - Bridge 100 USDC from Base to Polygon
        - I want to exchange 20 USDC on SOLANA to USDC on Base
        - Bridge 0.01 SOL  Solana to USDC on Base
        - Bridge $1 of SOL on Solana to USDC on Base
    """
    # check if chains are supported
    try:
        transaction_type = (
            TransactionType.BRIDGE if from_chain != to_chain else TransactionType.SWAP
        )

        thought_message = (
            f"Validating chain: {from_chain}..."
            if transaction_type == TransactionType.SWAP
            else f"Validating chains: {from_chain} and {to_chain}..."
        )
        save_agent_thought(chat_id=chat_id, thought=thought_message)

        if not supports_bridge(from_chain) or not supports_bridge(to_chain):
            raise ValueError(
                "Chains are not supported for bridging. Available chains are: "
                + ", ".join(supported_chains)
            )

        if not from_amount or float(from_amount) == 0:
            return "Please specify the amount you want to bridge or swap"

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Validating {from_token_symbol} and {to_token_symbol}...",
        )

        from_token_info = tokens_service.get_token_metadata(
            chain=str(from_chain), token=from_token_symbol
        )
        if not from_token_info:
            return f"The input token {from_token_symbol} on {from_chain} is not supported. Try again with a different token."

        to_token_info = tokens_service.get_token_metadata(
            chain=str(to_chain), token=to_token_symbol
        )
        if not to_token_info:
            return f"The output token {to_token_symbol} on {to_chain} is not supported. Try again with a different token."

        if is_usd:
            save_agent_thought(
                chat_id=chat_id,
                thought=f"Converting {from_amount} USD to {from_token_symbol}...",
            )
            from_amount = get_token_amount_from_usd(
                chain=from_chain, token=from_token_info, usd_amount=from_amount
            )

        evm_wallet_address = get_request_ctx(
            parentKey=chat_id, key="evm_wallet_address"
        )
        solana_wallet_address = get_request_ctx(
            parentKey=chat_id, key="solana_wallet_address"
        )
        allowance_type = get_request_ctx(parentKey=chat_id, key="allowance")
        slippage = str(
            Decimal(get_request_ctx(parentKey=chat_id, key="slippage") or 1) / 100
        )  # 0.5 -> 0.005

        if use_frontend_quoting:
            save_ui_message(
                chat_id=chat_id,
                component=TransactionType.BRIDGE.value,
                renderData={
                    "from_token": from_token_info,
                    "to_token": to_token_info,
                    "from_amount": from_amount,
                    "wallet_address": evm_wallet_address,
                    "solana_address": solana_wallet_address,
                    "from_chain": from_chain,
                    "to_chain": to_chain,
                    "transaction_type": transaction_type.value,
                },
                thought=f"Initiated {transaction_type.value.lower().capitalize()} successfully",
                isFinalThought=True,
            )
            return f"I've initiated the quoting proccess for your exchange transaction between {from_token_symbol} on {from_chain} and {to_token_symbol} on {to_chain}."
        else:
            if not evm_wallet_address and not solana_wallet_address:
                return "No wallet address found."

            from_token_amount = from_amount
            url = f"{FIREBASE_SERVER_ENDPOINT}/quote"
            params = {
                "chatId": chat_id,
                "userId": get_request_ctx(parentKey=chat_id, key="user_id") or "",
                "protocol": "LIFI",
                "walletAddress": evm_wallet_address,
                "solanaAddress": solana_wallet_address,
                "fromChainName": from_chain,
                "toChainName": to_chain,
                "fromTokenSymbolOrAddress": from_token_info["contract_address"],
                "toTokenSymbolOrAddress": to_token_info["contract_address"],
                "fromAmount": from_token_amount,
                "slippage": slippage,
                "allowanceType": allowance_type,
                "transactionType": transaction_type.value,
            }

            response = requests.post(url, json=params)
            if response.status_code != 200:
                response.raise_for_status()
            return response.json()
    except requests.exceptions.HTTPError as http_err:
        error_message = response.content.decode() if response.content else str(http_err)
        return f"There was an error building the exchange quote between {from_token_symbol} on {from_chain} and {to_token_symbol} on {to_chain}: {error_message}"
    except Exception as e:
        return f"There was an error building the exchange quote between {from_token_symbol} on {from_chain} and {to_token_symbol} on {to_chain}: {e}"


# used internally
def get_token_amount_from_usd(
    chain: Annotated[str, "The name of the chain"],
    token: Annotated[dict, "The token metadata"],
    usd_amount: Annotated[str, "The amount in USD"],
):
    """
    This function gets the token amount from the USD amount.

    # Parameters:
    - chain (str): The name of the chain
    - token (dict): the Token metadata
    - usd_amount (str): The amount in USD

    # Returns:
    - str: The amount of the token
    """
    try:
        token_symbol = token.get("symbol", "")
        token_price_response = prices_service.get_token_price_from_provider(
            chain, token.get("contract_address", ""), PriceProviderType.LIFI
        )
        price = float(token_price_response["price"])
        if price == 0:
            raise ValueError(f"Error fetching price for {token_symbol} on {chain}")
        return float(usd_amount) / float(price)
    except Exception as e:
        raise Exception(
            f"There was an error converting {usd_amount} USD to {token_symbol} on {chain}: {e}"
        )
