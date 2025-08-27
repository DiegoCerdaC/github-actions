import requests
from typing import Annotated, List, Dict, Union
from config import FIREBASE_SERVER_ENDPOINT
from utils.firebase import get_request_ctx

BASE_URL = f"{FIREBASE_SERVER_ENDPOINT}/lpServer"


def get_token_b_needed_amount(
    pool_address: Annotated[str, "Address of the Liquidity Pool"],
    token_a_amount: Annotated[str, "Amount of token A user wants to deposit"],
    token_a_address: Annotated[str, "Address of the token A"],
):
    url = f"{BASE_URL}/liquidity-pool/token-b-needed-amount?poolAddress={pool_address}&amount={token_a_amount}&tokenAAddress={token_a_address}"
    response = requests.get(url=url)
    response.raise_for_status()
    return response.json()


def get_user_positions_in_pool_address(
    pool_address: Annotated[str, "Address of the Liquidity Pool"],
    wallet_address: Annotated[str, "User's Solana Wallet Address"],
):
    url = f"{BASE_URL}/liquidity-pool/positions?poolAddress={pool_address}&walletAddress={wallet_address}"
    response = requests.get(url=url)
    response.raise_for_status()
    return response.json()


def add_liquidity(
    chat_id: Annotated[str, "The current chat id"],
    pool_address: Annotated[str, "Address of the Liquidity Pool"],
    wallet_address: Annotated[str, "User's Solana Wallet Address"],
    amount: Annotated[str, "Amount user wants to deposit"],
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
    from_token: Annotated[Dict[str, Union[str, float]], "Token A information"] = None,
    from_token_b: Annotated[Dict[str, Union[str, float]], "Token B information"] = None,
    from_token_usd: Annotated[float, "Amount of token A in USD"] = 0,
    pool_name: Annotated[str, "Name of the pool"] = "",
    pool_apr: Annotated[float, "APR of the pool"] = 0,
    pool_apy: Annotated[float, "APY of the pool"] = 0,
    current_pool_price: Annotated[float, "Current price of the pool"] = 0,
    is_relocating: Annotated[
        bool, "Flag to indicate if the user is relocating liquidity"
    ] = False,
):
    try:
        url = f"{BASE_URL}/liquidity-pool/add"
        response = requests.post(
            url=url,
            json={
                "userId": get_request_ctx(chat_id, "user_id") or "",
                "poolAddress": pool_address,
                "walletAddress": wallet_address,
                "amount": float(amount),
                "type": type,
                "amountB": float(amountB) if amountB != "" else None,
                "positionAddress": position_address,
                "fromToken": from_token,
                "fromTokenB": from_token_b,
                "fromTokenUsd": from_token_usd,
                "poolName": pool_name,
                "poolApr": pool_apr,
                "poolApy": pool_apy,
                "currentPoolPrice": current_pool_price,
                "isRelocating": is_relocating,
                "chatId": chat_id,
            },
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        error_message = response.content.decode() if response.content else str(http_err)
        raise Exception(
            f"There was an error building the deposit transaction on Meteora: {error_message}"
        )
    except Exception as e:
        raise Exception(
            f"There was an error building the deposit transaction on Meteora: {e}"
        )


def remove_liquidity(
    pool_address: Annotated[str, "Address of the Liquidity Pool"],
    wallet_address: Annotated[str, "User's Solana Wallet Address"],
    type: Annotated[
        str, "Type of withdrawal. Can be 'single'or 'all'. Default is 'all'"
    ] = "all",
    position_address: Annotated[
        str, "Existing Position Address. Only apply if 'type' is 'single'."
    ] = "",
    percentage_to_withdraw: Annotated[
        str,
        "Percentage to withdraw. Example 25 / 50 / 100. Use 100 to withdraw all liquidity",
    ] = 100,
):
    url = f"{BASE_URL}/liquidity-pool/remove"
    response = requests.post(
        url=url,
        json={
            "poolAddress": pool_address,
            "walletAddress": wallet_address,
            "type": type,
            "positionAddress": position_address,
            "percentageToWithdraw": percentage_to_withdraw,
        },
    )
    response.raise_for_status()
    return response.json()


def claim_swap_fees(
    pool_address: Annotated[str, "Address of the Liquidity Pool"],
    wallet_address: Annotated[str, "User's Solana Wallet Address"],
    chat_id: Annotated[str, "The current chat id"],
):
    url = f"{BASE_URL}/liquidity-pool/claim-swap-fee"
    try:
        response = requests.post(
            url=url,
            json={
                "userId": get_request_ctx(chat_id, "user_id") or "",
                "poolAddress": pool_address,
                "walletAddress": wallet_address,
                "chatId": chat_id,
            },
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise Exception(
            f"There was an error claiming your swap fees. Please try again later: {e}"
        )


def search_pools_with_user_liquidity(
    wallet_address: Annotated[str, "User's Solana Wallet Address"],
    pool_list: Annotated[
        List[Dict[str, Union[str, float]]], "List of pools to search for user liquidity"
    ],
    is_claiming_fees: Annotated[
        bool, "Whether the user is claiming fees or not"
    ] = False,
):
    url = f"{BASE_URL}/liquidity-pool/search-pools-with-user-liquidity"
    response = requests.post(
        url=url,
        json={
            "walletAddress": wallet_address,
            "poolsList": pool_list,
            "isClaimingFees": is_claiming_fees,
        },
    )
    response.raise_for_status()
    return response.json()
