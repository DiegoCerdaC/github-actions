import requests
from typing import List, Annotated, Dict, Any
from utils.firebase import save_ui_message
from services.chains import get_all_native_tokens


def get_token_info(token_address: str):
    try:
        response = requests.get(
            f"https://api.dexscreener.io/latest/dex/tokens/{token_address}", headers={}
        )
        return response.json()
    except Exception as e:
        return None


def get_dexscreener_latest_tokens(
    chat_id: str,
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    Gets the latest tokens added to Dexscreener.
    # Parameters:
    - chat_id (str): The current chat id

    # Returns:
    - str: A JSON-formatted response from the AI agent containing the latest tokens added to Dexscreener.
    """

    try:
        response = requests.get(
            "https://api.dexscreener.com/token-profiles/latest/v1", headers={}
        )
        latest_tokens = response.json()

        list_to_return = []
        for token in latest_tokens:
            if len(list_to_return) == 10:
                break
            token_info = get_token_info(token["tokenAddress"])
            if token_info is None:
                continue

            list_to_return.append(
                {
                    "name": token_info["pairs"][0]["baseToken"]["name"],
                    "symbol": token_info["pairs"][0]["baseToken"]["symbol"],
                    "address": token["tokenAddress"],
                    "chain": token["chainId"],
                    "logoUri": token.get("icon", ""),
                    "description": token.get("description", ""),
                    "dexscreener_url": token.get("url", ""),
                    "website": next(
                        (
                            link.get("url")
                            for link in token.get("links", [])
                            if link.get("label") == "Website"
                        ),
                        None,
                    ),
                    "twitter": next(
                        (
                            link.get("url")
                            for link in token.get("links", [])
                            if link.get("type") == "twitter"
                        ),
                        None,
                    ),
                }
            )

        if use_frontend_quoting:
            save_ui_message(
                chat_id=chat_id,
                component="dexscreener_list",
                renderData={
                    "title": "Latest Tokens",
                    "tokens": list_to_return,
                },
            )
            return f"The latest tokens added on Dexscreener were fetched succesfully.: {list_to_return}"
        else:
            return list_to_return
    except Exception as e:
        return f"There was an error fetching the latest tokens on Dexscreener: {str(e)}. Please try again in a few minutes."


def process_boosted_tokens(tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process tokens by sorting and removing duplicates."""
    # Sort by totalAmount in descending order
    sorted_tokens = sorted(tokens, key=lambda x: x["totalAmount"], reverse=True)

    # Remove duplicates keeping the first occurrence (highest totalAmount)
    unique_tokens = {token["tokenAddress"]: token for token in sorted_tokens}.values()
    return list(unique_tokens)


def get_dexscreener_latest_boosted_tokens(
    chat_id: str,
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    Gets the latest boosted tokens on Dexscreener.
    # Parameters:
    - chat_id (str): The current chat id

    # Returns:
    - str: A JSON-formatted response from the AI agent containing the latest boosted tokens on Dexscreener.
    """
    try:
        response = requests.get(
            "https://api.dexscreener.com/token-boosts/latest/v1", headers={}
        )
        boosted_tokens = response.json()
        boosted_tokens = process_boosted_tokens(boosted_tokens)
        list_to_return = []
        for token in boosted_tokens:
            # Get the top 10 boosted tokens (by totalAmount and tokens where we could fetch the token info)
            if len(list_to_return) == 10:
                break
            token_info = get_token_info(token["tokenAddress"])
            if token_info is None:
                continue
            list_to_return.append(
                {
                    "name": token_info["pairs"][0]["baseToken"]["name"],
                    "symbol": token_info["pairs"][0]["baseToken"]["symbol"],
                    "address": token["tokenAddress"],
                    "chain": token["chainId"],
                    "logoUri": token.get("icon", ""),
                    "description": token.get("description", ""),
                    "boostedAmount": token["totalAmount"],
                    "website": next(
                        (
                            link.get("url")
                            for link in token.get("links", [])
                            if link.get("label") == "Website"
                        ),
                        None,
                    ),
                    "twitter": next(
                        (
                            link.get("url")
                            for link in token.get("links", [])
                            if link.get("type") == "twitter"
                        ),
                        None,
                    ),
                }
            )

        if use_frontend_quoting:
            save_ui_message(
                chat_id=chat_id,
                component="dexscreener_list",
                renderData={
                    "title": "Latest Boosted Tokens",
                    "tokens": list_to_return,
                },
            )
            return "The latest boosted tokens on Dexscreener were fetched"
        else:
            return list_to_return

    except Exception as e:
        return f"There was an error fetching the latest boosted tokens on Dexscreener: {str(e)}. Please try again in a few minutes."


def get_dexscreener_most_boosted_tokens(
    chat_id: str,
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    Gets the top 10 most boosted tokens on Dexscreener.
    # Parameters:
    - chat_id (str): The current chat id

    # Returns:
    - str: A JSON-formatted response from the AI agent containing the top 10 most boosted tokens on Dexscreener.
    """
    try:
        response = requests.get(
            "https://api.dexscreener.com/token-boosts/top/v1", headers={}
        )
        most_boosted_tokens = response.json()

        list_to_return = []
        for token in most_boosted_tokens:
            if len(list_to_return) == 10:
                break
            token_info = get_token_info(token["tokenAddress"])
            if token_info is None:
                continue
            list_to_return.append(
                {
                    "name": token_info["pairs"][0]["baseToken"]["name"],
                    "symbol": token_info["pairs"][0]["baseToken"]["symbol"],
                    "address": token["tokenAddress"],
                    "logoUri": token["icon"],
                    "chain": token["chainId"],
                    "description": token.get("description", ""),
                    "boostedAmount": token["totalAmount"],
                    "website": next(
                        (
                            link.get("url")
                            for link in token.get("links", [])
                            if link.get("label") == "Website"
                        ),
                        None,
                    ),
                    "twitter": next(
                        (
                            link.get("url")
                            for link in token.get("links", [])
                            if link.get("type") == "twitter"
                        ),
                        None,
                    ),
                }
            )

        if use_frontend_quoting:
            save_ui_message(
                chat_id=chat_id,
                component="dexscreener_list",
                renderData={
                    "title": "Top Boosted Tokens",
                    "tokens": list_to_return,
                },
            )
            return "The top 10 most boosted tokens on Dexscreener were fetched"
        else:
            return list_to_return
    except Exception as e:
        return f"There was an error fetching the most boosted tokens on Dexscreener: {str(e)}, please try again in a few minutes."


def get_dexscreener_token_pair_info(
    chat_id: str, token_a_symbol: str, token_b_symbol: str
):
    """
    Retrieves information about a token pair from Dexscreener.
    # Parameters:
    - chat_id (str): The current chat id
    - token_a_symbol (str): The symbol of the first token.
    - token_b_symbol (str): The symbol of the second token. If token_b_symbol is empty, default to SOL. Or else, use USDC if token_a_symbol is SOL.

    # Returns:
    - str: A JSON-formatted response from the AI agent containing token pair information.
    """
    try:
        native_symbols = get_all_native_tokens()
        token_a_symbol_upper = token_a_symbol.upper()
        token_b_symbol_upper = token_b_symbol.upper()

        # Check if either token_a_symbol or token_b_symbol is a native symbol
        tokens = [token_a_symbol_upper, token_b_symbol_upper]
        non_native_tokens = [t for t in tokens if t.upper() not in native_symbols]

        if len(non_native_tokens) == 1:
            search_term = non_native_tokens[0]
        else:
            search_term = f"{token_a_symbol}+{token_b_symbol}"

        url = f"https://api.dexscreener.com/latest/dex/search?q={search_term}"
        response = requests.get(url, headers={})

        pairs_info = response.json()["pairs"]

        # Try to find a pair where token_a is baseToken and token_b is quoteToken
        pair_info = None
        for pair in pairs_info:
            base_symbol = pair.get("baseToken", {}).get("symbol", "").upper()
            quote_symbol = pair.get("quoteToken", {}).get("symbol", "").upper()
            if (
                base_symbol == token_a_symbol_upper
                and quote_symbol == token_b_symbol_upper
            ):
                pair_info = pair
                break

        # If not found, try the reverse (token_b as baseToken, token_a as quoteToken)
        if pair_info is None:
            for pair in pairs_info:
                base_symbol = pair.get("baseToken", {}).get("symbol", "").upper()
                quote_symbol = pair.get("quoteToken", {}).get("symbol", "").upper()
                if (
                    base_symbol == token_b_symbol_upper
                    and quote_symbol == token_a_symbol_upper
                ):
                    pair_info = pair
                    break

        if pair_info is None:
            return "We couldn't find any pair with the tokens you provided, please try again with different tokens."
        token_a_info = get_token_info(pair_info["baseToken"]["address"])
        token_b_info = get_token_info(pair_info["quoteToken"]["address"])

        info_to_return = {
            "token_a_name": token_a_info["pairs"][0]["baseToken"]["name"],
            "token_a_symbol": token_a_info["pairs"][0]["baseToken"]["symbol"],
            "token_a_address": pair_info["baseToken"]["address"],
            "token_a_logoUri": pair_info["info"]["imageUrl"],
            "token_b_name": token_b_info["pairs"][0]["baseToken"]["name"],
            "token_b_symbol": token_b_info["pairs"][0]["baseToken"]["symbol"],
            "token_b_address": pair_info["quoteToken"]["address"],
            "marketCap": float(pair_info["marketCap"] / 10**6),
            "volume": float(pair_info["volume"]["h24"]),
            "priceNative": pair_info["priceNative"],
            "priceUsd": pair_info["priceUsd"],
            "dexId": pair_info["dexId"],
            "24_hrs_buys": pair_info["txns"]["h24"]["buys"],
            "24_hrs_sells": pair_info["txns"]["h24"]["sells"],
            "24_hrs_price_change": pair_info["priceChange"]["h24"],
            "url": pair_info.get("url", None),
        }
        if chat_id:
            save_ui_message(
                chat_id=chat_id,
                component="dexscreener_token_pair_info",
                renderData=info_to_return,
                thought="Task completed successfully",
                isFinalThought=True,
            )
        return info_to_return

    except Exception as e:
        return f"There was an error fetching the token pair info on Dexscreener, please try again in a few minutes: {e}"


def get_dexscreener_token_pair_info_by_chain_and_token_address(
    chat_id: str,
    chain_id: str,
    token_address: str,
):
    """
    Retrieves information about a token pair from Dexscreener.
    # Parameters:
    - chat_id (str): The current chat id
    - chain_id (str): The chain id of the first token.
    - token_a_address (str): The address of the first token.
    - token_b_address (str): The address of the second token.

    # Returns:
    - dict: A dictionary containing token pair information.
    """
    try:
        url = f"https://api.dexscreener.com/token-pairs/v1/{chain_id}/{token_address}"
        response = requests.get(url, headers={})
        pairs = response.json()

        if not pairs or len(pairs) == 0:
            return "We couldn't find any pair with the tokens you provided, please try again with different tokens."

        # Find the pair with the highest market cap
        target_pair = None
        max_market_cap = 0

        for pair in pairs:
            current_market_cap = pair.get("marketCap", 0)
            if current_market_cap > max_market_cap:
                max_market_cap = current_market_cap
                target_pair = pair

        if not target_pair:
            return "We couldn't find a pair with market cap information, please try again in a few minutes."

        # Get token info for both tokens
        token_a_info = get_token_info(target_pair["baseToken"]["address"])
        token_b_info = get_token_info(target_pair["quoteToken"]["address"])

        if not token_a_info or not token_b_info:
            return "We couldn't fetch complete token information, please try again in a few minutes."

        info_to_return = {
            "token_a_name": target_pair["baseToken"]["name"],
            "token_a_symbol": target_pair["baseToken"]["symbol"],
            "token_a_address": target_pair["baseToken"]["address"],
            "token_a_logoUri": target_pair.get("info", {}).get("imageUrl", ""),
            "token_b_name": target_pair["quoteToken"]["name"],
            "token_b_symbol": target_pair["quoteToken"]["symbol"],
            "token_b_address": target_pair["quoteToken"]["address"],
            "marketCap": float(target_pair.get("marketCap", 0) / 10**6),
            "volume": float(target_pair.get("volume", {}).get("h24", 0)),
            "priceNative": target_pair.get("priceNative", 0),
            "priceUsd": target_pair.get("priceUsd", 0),
            "dexId": target_pair.get("dexId", ""),
            "24_hrs_buys": target_pair.get("txns", {}).get("h24", {}).get("buys", 0),
            "24_hrs_sells": target_pair.get("txns", {}).get("h24", {}).get("sells", 0),
            "24_hrs_price_change": target_pair.get("priceChange", {}).get("h24", 0),
            "url": target_pair.get("url", ""),
        }

        save_ui_message(
            chat_id=chat_id,
            component="dexscreener_token_pair_info",
            renderData=info_to_return,
            thought="Task completed successfully",
            isFinalThought=True,
        )
        return info_to_return

    except Exception as e:
        return f"There was an error fetching the token pair info on Dexscreener: {str(e)}. Please try again in a few minutes."


def get_multiple_tokens_pair_info(token_symbols: List[str], chat_id: str | None = None):
    """Get the pair info for multiple tokens."""
    results = {}
    for token_symbol in token_symbols:
        pair_info = get_dexscreener_token_pair_info(
            chat_id=chat_id,
            token_a_symbol=token_symbol,
            token_b_symbol="SOL",
        )
        if not isinstance(pair_info, dict):
            continue
        token_address = pair_info.get("token_a_address")
        if not token_address:
            continue
        pair_info["is_possible_rug"] = is_possible_rug(token_address)

        results[token_symbol] = pair_info
    return results


def is_possible_rug(token_address: str):
    """Check if a token is marked as 'Good' on rugcheck.xyz."""
    try:
        url = f"https://api.rugcheck.xyz/v1/tokens/{token_address}/report/summary"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data.get("score", 0) > 1000:
            return True
        return False
    except Exception as e:
        print(f"Error checking rugcheck.xyz for {token_address}: {e}")
        return False
