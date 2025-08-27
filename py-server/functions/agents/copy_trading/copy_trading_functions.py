from typing import Annotated, Any
from config import MORALIS_API_KEY
from utils.firebase import save_ui_message, save_agent_thought
import requests
from utils.blockchain_utils import is_solana


def copy_trading(user_wallet_address: str, tracked_wallet_address: str, chat_id: str):
    """
    Follow and copy latest trades from a tracked wallet in real-time
    This function is used to copy and save the last trade of a tracked wallet to the user's wallet document.
    If the tracked wallet has made a trade or more, it will return the latest trades and the user can use the jupiter agent or lifi agent to copy the trade.
    If the tracked wallet has not made a trade, it will return a message saying that the wallet has not made any changes since the last transaction.

    # Parameters:
    - user_wallet_address (str): The wallet address of the user.
    - tracked_wallet_address (str): The wallet address of the tracked wallet.
    - chat_id (str): The current chat id

    # Returns:
    - The latest trades from the tracked wallet.
    """
    try:
        user_wallet_address = user_wallet_address.lower()
        if not is_solana(tracked_wallet_address):
            return "Invalid Tracked Wallet Address (not a Solana address). Please specify a SOLANA Wallet address, as this agent doesn't support EVM wallets for copy-trading."

        swaps = get_swaps_by_wallet_address(
            chat_id, tracked_wallet_address, use_frontend_quoting=True, limit=5
        )
        return swaps
    except Exception as e:
        return "Error saving transaction to database"


# Use this function when we have no history of the wallet. We only save the last transaction.
def get_last_swap_by_wallet_address(wallet_address, chat_id):
    try:
        swap = get_swaps_by_wallet_address(wallet_address, limit=1, chat_id=chat_id)
        if swap.get("result", []):
            return swap.get("result", [])[0]
        else:
            return None
    except Exception as e:
        return None


def get_latest_swaps_by_wallet_address(
    wallet_address, last_transaction_date, transaction_hash, chat_id
):
    try:
        swaps = get_swaps_by_wallet_address(
            wallet_address, limit=100, from_date=last_transaction_date, chat_id=chat_id
        )
        if swaps:
            new_swaps = []
            for swap in swaps:
                if swap.get("transactionHash") != transaction_hash:
                    new_swaps.append(swap)
            return new_swaps

        else:

            return None
    except Exception as e:
        return None


def get_swaps_by_wallet_address(
    chat_id: Annotated[str, "The current chat id"],
    wallet_address: Annotated[str, "The wallet address to get the swaps from"],
    network: Annotated[str, "The network to get the swaps from"] = "mainnet",
    from_date: Annotated[str, "The start date to get the swaps from"] = "",
    to_date: Annotated[str, "The end date to get the swaps from"] = "",
    cursor: Annotated[str, "The cursor to get the swaps from"] = "",
    limit: Annotated[int, "The limit of swaps to get"] = 100,
    order: Annotated[str, "The order of the swaps"] = "DESC",
    transaction_types: Annotated[
        str, "The transaction types to get the swaps from"
    ] = "buy,sell",
    token_address: Annotated[str, "The token address to get the swaps from"] = "",
    use_frontend_quoting: Annotated[
        bool, "Whether to send the UI component with the swaps"
    ] = False,
) -> Any:
    """
    Gets a list of the latest swaps from a wallet address.
    # Parameters:
    - chat_id (str): The current chat id
    - wallet_address (str): The wallet address to get the swaps from.
    - network (str): The network to get the swaps from.
    - from_date (str): The start date to get the swaps from.
    - to_date (str): The end date to get the swaps from.
    - cursor (str): The cursor to get the swaps from.
    - limit (int): The limit of swaps to get. By default is 100.
    - order (str): The order of the swaps. By default is DESC.
    - transaction_types (str): The transaction types to get the swaps from. By default is buy,sell.
    - token_address (str): The token address to get the swaps from. By default is empty.
    - use_frontend_quoting (bool): Whether to send the UI component with the swaps. By default is False.

    # Returns:
    - The list of swaps.
    """
    try:
        save_agent_thought(
            chat_id=chat_id,
            thought="Tracking wallet...",
        )

        if not is_solana(wallet_address):
            raise Exception("Invalid Wallet Address (not a Solana address).")

        base_url = f"https://solana-gateway.moralis.io/account/{network}/{wallet_address}/swaps"

        params = {
            "fromDate": from_date,
            "toDate": to_date,
            "cursor": cursor,
            "limit": limit,
            "order": order,
            "transactionTypes": transaction_types,
            "tokenAddress": token_address,
        }
        params = {k: v for k, v in params.items() if v is not None and v != ""}

        response = requests.get(
            base_url,
            headers={"X-API-KEY": MORALIS_API_KEY},
            params=params,
        )
        response.raise_for_status()
        swaps = response.json()

        new_swaps = []
        logo_map = {
            "USDC": "https://assets.coingecko.com/coins/images/6319/standard/usdc.png?1696506694",
            "SOL": "https://s2.coinmarketcap.com/static/img/coins/64x64/5426.png",
            "USDT": "https://s2.coinmarketcap.com/static/img/coins/64x64/825.png",
            "GRIFT": "https://assets.coingecko.com/coins/images/52598/standard/4.png?1733741120",
        }

        save_agent_thought(
            chat_id=chat_id,
            thought="Preparing swaps...",
        )

        transaction_hash_list = []
        for swap in swaps.get("result", []):
            if swap.get("transactionHash") not in transaction_hash_list:
                for side in ["sold", "bought"]:

                    symbol = swap.get(side).get("symbol")
                    if symbol in logo_map:
                        swap[side]["logo"] = logo_map[symbol]
                new_swaps.append(swap)
                transaction_hash_list.append(swap.get("transactionHash"))
        if use_frontend_quoting:
            save_ui_message(
                chat_id=chat_id,
                renderData=new_swaps,
                component="copy_trading_options",
                thought=(f"Wallet tracked successfully"),
                isFinalThought=True,
            )
            return "Swaps retrieved successfully"

        return new_swaps
    except Exception as e:
        return f"Error in getting swap transactions for wallet {wallet_address}: {e}"
