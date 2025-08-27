import requests
from enum import Enum
from config import FIREBASE_SERVER_ENDPOINT


class PriceProviderType(str, Enum):
    JUPITER = "jupiter"
    LIFI = "lifi"


def get_token_price_from_provider(
    chain_name: str, token_address: str, provider: PriceProviderType
) -> dict:
    """
    This function fetches the token price from a provider.

    Args:
        chain_name (str): The name of the chain.
        token_address (str): The address of the token.
        provider (str): The name of the price provider (lifi, jupiter, decent, etc)

    Returns:
        dict: The response from the provider.
         Example response   {
            "price": 105161.87325930696,
            "symbol": "ETH",
            "decimals": 18,
            "tokenAddress": "0x0000000000000000000000000000000000000000",
            "chainId": "1",
            "chainName": "Ethereum",
            "chainReference": "oE3NJzHtktvuD0DFOh4q",
            "priceProvider": "jupiter",
            "updatedAt": 1738277707734
        }
    """
    try:
        response = requests.get(
            f"{FIREBASE_SERVER_ENDPOINT}/getTokenPrice?tokenAddress={token_address}&chain={chain_name}&provider={provider.value}"
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch token price from provider {provider.value}: {e}")
        return {"price": 0}
