import json
from typing import Annotated
from decimal import Decimal
from enum import Enum
import requests
from services.chains import call_chains_service

from utils.firebase import (
    get_request_ctx,
    set_request_ctx,
    save_agent_thought,
    get_enso_supported_chains_and_protocols,
    get_enso_supported_tokens,
    save_ui_message,
)
import services.prices as prices_service
from services.prices import PriceProviderType
from config import FIREBASE_SERVER_ENDPOINT


def _check_and_record_for_evaluation(function_name: str, params: dict) -> str | None:
    """
    Checks for evaluation_mode. If active, records the function call and may return a status message.
    Args:
    - function_name (str): The name of the function being called.
    - params (dict): A dictionary of the parameters passed to the function (e.g., from locals()).
    Returns:
    - str | None: An evaluation status message if execution should stop, otherwise None.
    """
    chat_id = params.get("chat_id")
    if not chat_id:
        return None

    is_evaluation = get_request_ctx(chat_id, "evaluation_mode") or False
    if not is_evaluation:
        return None

    function_call = {"function": function_name, "parameters": params}
    current_calls = get_request_ctx(chat_id, "function_calls") or []
    current_calls.append(function_call)
    set_request_ctx(chat_id, "function_calls", current_calls)

    return f"Evaluation mode: {function_name} function called and registered parameters for testing."


def is_protocol_supported(protocol_slug):
    supported_protocols = get_enso_supported_chains_and_protocols()
    protocol_slug_lower = protocol_slug.lower()

    for chain_id, chain_data in supported_protocols.items():
        protocols = chain_data.get("protocols", [])
        protocols_lower = [p.lower() for p in protocols]

        # Exact match
        if protocol_slug_lower in protocols_lower:
            return True

        # Partial match (e.g., "aave" should match "aave-v3", "aave-v2")
        for protocol in protocols_lower:
            if protocol_slug_lower in protocol or protocol.startswith(
                protocol_slug_lower
            ):
                return True

    return False


def is_chain_supported(chain):
    """
    Check if a chain is supported for Enso protocols
    Args:
        chain (str): Chain name or ID (e.g., "BASE", "ethereum", "8453")
    Returns:
        bool: True if chain is supported, False otherwise
    """
    try:
        # Get supported protocols from Firestore
        supported_chains_and_protocols = get_enso_supported_chains_and_protocols()

        if not supported_chains_and_protocols:
            return False

        chain_lower = chain.lower()

        # Check if chain is already a chain_id (numeric string)
        if chain.isdigit():
            return chain in supported_chains_and_protocols

        # Check by chain name (case-insensitive)
        for chain_id, chain_data in supported_chains_and_protocols.items():
            chain_name = chain_data.get("chain_name", "").lower()
            if chain_lower == chain_name:
                return True

        # If not found by name, try to get chain ID and check
        try:
            chain_id = call_chains_service(method="getChainId", chainName=chain)
            if chain_id:
                return str(chain_id) in supported_chains_and_protocols
        except:
            pass

        return False
    except Exception as e:
        print(f"Error checking if chain {chain} is supported: {e}")
        return False


def defi_quote(
    token: Annotated[
        str, "The token address or symbol to deposit from or withdraw to."
    ],
    chat_id: Annotated[str, "The current chat id"],
    is_withdraw: Annotated[bool, "Whether to withdraw or deposit"],
    amount: Annotated[str, "The amount of the token to deposit or withdraw."] = None,
    from_chain: Annotated[str, "Chain name (optional)"] = None,
    protocol: Annotated[str, "Protocol name (optional)"] = None,
    defi_token_symbol: Annotated[
        str, "Token symbol (optional) to deposit to or withdraw from"
    ] = None,
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
):
    """
    Get a quote for a DeFi Transaction using the Enso protocol.
    Automatically finds the best matching token based on provided filters.
    If multiple tokens match, selects the one with highest APY.

    # Parameters:
    - token (str): The symbol or address of the token to deposit from or withdraw to
    - chat_id (str): The current chat id
    - is_withdraw (bool): Whether to withdraw or deposit
    - amount (str, optional): The amount of the token to deposit or withdraw.
    - from_chain (str, optional): The name of the chain to filter by
    - protocol (str, optional): The protocol name to filter by (e.g., "aave", "morpho")
    - defi_token_symbol (str, optional): The defi token symbol to deposit to or withdraw from

    # Returns:
    - str: The quote for the transaction
    """

    eval_message = _check_and_record_for_evaluation("defi_quote", locals())
    if eval_message:
        return eval_message

    save_agent_thought(
        chat_id=chat_id,
        thought=f"Initiating process to get you a quote for your {is_withdraw and 'withdraw' or 'deposit'}...",
    )

    save_agent_thought(
        chat_id=chat_id,
        thought=f"Getting matching tokens for your request...",
    )

    # Find the best matching token using filters
    matching_tokens = get_matching_defi_tokens(
        chain_name=from_chain, protocol=protocol, symbol=defi_token_symbol
    )

    if not matching_tokens:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"No matching tokens found for the specified criteria",
            isFinalThought=True,
        )
        raise ValueError(f"No matching tokens found for the specified criteria")

    # Select the first token (highest APY)
    selected_defi_token = matching_tokens[0]
    to_defi_token_address = selected_defi_token["token"]["address"]

    # Validate chain if provided
    if from_chain:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Validating chain {from_chain}...",
        )

        if not is_chain_supported(from_chain):
            save_agent_thought(
                chat_id=chat_id,
                thought=f"Chain {from_chain} is not supported",
                isFinalThought=True,
            )
            raise ValueError(f"Chain {from_chain} is not supported")

    from_wallet_address = get_request_ctx(chat_id, "evm_wallet_address")

    slippage = str(
        Decimal(get_request_ctx(chat_id, "slippage") or 1) * 100
    )  # 0.5 -> 50

    if not use_frontend_quoting:
        if not amount:
            raise ValueError("Amount is required when using backend quoting")

        if not from_chain:
            raise ValueError("From chain is required when using backend quoting")

        allowance_type = get_request_ctx(chat_id, "allowance")

        url = f"{FIREBASE_SERVER_ENDPOINT}/quote"
        params = {
            "chatId": chat_id,
            "userId": get_request_ctx(chat_id, "user_id") or "",
            "protocol": "ENSO",
            "walletAddress": from_wallet_address,
            "fromChainName": from_chain,
            "toChainName": from_chain,
            "fromTokenSymbolOrAddress": token,
            "toTokenSymbolOrAddress": to_defi_token_address,
            "fromAmount": float(amount),
            "slippage": slippage,
            "allowanceType": allowance_type,
        }
        response = requests.post(url, json=params)
        if response.status_code != 200:
            response.raise_for_status()

        return response.json()

    else:
        # If is withdrawing without specifying the defi_token and protocol, the frontend will show the highest balance
        # ex user just saying "withdraw what I have deposited"
        if is_withdraw and not defi_token_symbol and not protocol:
            to_defi_token_address = None

        save_ui_message(
            chat_id=chat_id,
            component="enso",
            renderData={
                "token": token,
                "defi_token_symbol": to_defi_token_address or None,
                "amount": amount or None,
                "is_withdraw_mode": is_withdraw,
            },
            thought="Retrieving quote...",
            isFinalThought=True,
        )
        return f"I've started the process to make your {is_withdraw and 'withdraw' or 'deposit'} succesfully."


#############################################################
### TOKEN-RELATED UTILS
#############################################################
def get_matching_defi_tokens(
    chain_name: Annotated[str, "Name of the chain (optional)"] = None,
    protocol: Annotated[str, "Protocol name (optional)"] = None,
    symbol: Annotated[str, "Token symbol (optional)"] = None,
):
    """
    Get filtered list of defi tokens/positions/vaults from Enso database using optimized queries
    Filters are optional - if not provided, returns all tokens
    Always returns results sorted by APY (descending)

    Args:
        chain_name (str, optional): Filter by chain name (e.g., "BASE", "ethereum")
        protocol (str, optional): Filter by protocol (e.g., "aave", "morpho")
        symbol (str, optional): Filter by token symbol (e.g., "USDC", "ETH")

    Returns:
        list: Filtered and sorted list of token objects
    """
    # Get chain_id if chain_name is specified
    target_chain_id = None
    if chain_name:
        try:
            # Try to get chain_id from chain_name using chains service
            target_chain_id = call_chains_service(
                method="getChainId", chainName=chain_name
            )
        except:
            # If we can't get chain_id, use None and we pick all tokens
            target_chain_id = None
    # Use optimized query with filters applied at DB level
    filtered_tokens = get_enso_supported_tokens(
        chain_id=str(target_chain_id) if target_chain_id else None,
        project=protocol.lower() if protocol else None,
        symbol=symbol,
    )

    # If no results with filters, fallback to highest APY tokens
    if not filtered_tokens:
        # Get all tokens sorted by APY (descending)
        all_tokens = get_enso_supported_tokens()
        return all_tokens

    return filtered_tokens


def get_token_usd_amount(chain: str, token_address: str, token_amount: float):
    token_price_response = prices_service.get_token_price_from_provider(
        chain, token_address, PriceProviderType.LIFI
    )
    return float(Decimal(token_price_response["price"]) * Decimal(token_amount))
