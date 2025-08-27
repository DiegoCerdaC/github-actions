import requests
from config import FIREBASE_SERVER_ENDPOINT

def call_evm_blockchains_service(method: str, **params) -> dict:
    """
    Calls the new EVM Blockchains service endpoint with the given method and parameters.

    Args:
        method (str): The method to call in the chains service.
        **params: Additional parameters for the request.

    Returns:
        dict: The response from the service.
    """
    try:
        params["method"] = method
        response = requests.get(
            f"{FIREBASE_SERVER_ENDPOINT}/evmBlockchainsService", params=params
        )
        response.raise_for_status()

        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to call EVM Blockchains service: {e}")
        return {"error": "Failed to call EVM Blockchains service"}
