from enum import Enum
import requests
from google.cloud.firestore_v1.base_query import FieldFilter

from config import FIREBASE_SERVER_ENDPOINT
from utils.firebase import db


class ChainType(Enum):
    EVM = "EVM"
    SOLANA = "SOLANA"


def call_chains_service(method: str, **params) -> dict:
    """
    Calls the new chains service endpoint with the given method and parameters.

    Args:
        method (str): The method to call in the chains service.
        **params: Additional parameters for the request.

    Returns:
        dict: The response from the service.
    """
    try:
        params["method"] = method
        response = requests.get(
            f"{FIREBASE_SERVER_ENDPOINT}/callChainsService", params=params
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to call chains service: {e}")
        return {"error": "Failed to call chains service"}


def get_all_native_tokens():
    try:
        active_chains = (
            db.collection("chains")
            .where(filter=FieldFilter("ACTIVE", "==", True))
            .get()
        )
        # Only include non-empty symbols in the result
        native_tokens_symbol = []
        # Use a set to collect unique symbols
        native_tokens_symbol_set = set()
        for chain in active_chains:
            symbol = chain.to_dict().get("native_currency", {}).get("symbol", "")
            if symbol:
                native_tokens_symbol_set.add(symbol)
        native_tokens_symbol = list(native_tokens_symbol_set)

        return native_tokens_symbol
    except Exception as e:
        print("something went wrong getting all native tokens", e)
        return []
