import requests
from typing import Optional
from config import FIREBASE_SERVER_ENDPOINT


class TokenService:
    def __init__(self):
        self.base_url = FIREBASE_SERVER_ENDPOINT

    def get_token_metadata(
        self, token: Optional[str] = None, chain: Optional[str] = None
    ):
        """
        Get metadata of first token that matches the filters.
        Args:
            token (str, optional): Token, can be symbol or address
            chain (str, optional): Token chain name, can be 'name', 'doc id', or 'chain id'
        Raises:
            requests.RequestException: If there is an error in the request
        """

        token_list = self.get_token_list(token=token, chain=chain)
        return token_list[0] if token_list and len(token_list) > 0 else None

    def get_token_list(
        self, token: Optional[str] = None, chain: Optional[str] = None
    ) -> dict:
        """
        Get list of matching tokens.
        Args:
            name (str, optional): Token name
            chain (str, optional): Token chain
        Raises:
            requests.RequestException: If there is an error in the request
        """

        params = {"token": token if token else "", "chain": chain if chain else ""}
        try:
            response = requests.get(f"{self.base_url}/supportedTokens", params=params)
            if response.status_code != 200:
                return []
            return response.json()
        except (
            requests.exceptions.RequestException,
            requests.exceptions.JSONDecodeError,
        ):
            return []


tokens_service = TokenService()
