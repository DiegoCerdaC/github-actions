from enum import Enum
import requests
from config import FIREBASE_SERVER_ENDPOINT


class BalanceServiceType(Enum):
    EVM = "evm"
    SOLANA = "solana"


def get_wallet_balance(walletAddress: str, chainType: str) -> list:
    """
    Calls the new Balances service to get the balances for a wallet address and type
    """
    try:
        params = {"walletAddress": walletAddress, "chainType": chainType.lower()}
        response = requests.get(
            f"{FIREBASE_SERVER_ENDPOINT}/getWalletBalancesForAddress", params=params
        )
        response.raise_for_status()
        data = response.json()

        if "balances" in data:
            return data["balances"]
        else:
            return []
    except Exception as e:
        print(f"Error getting wallet balances: {e}")
        return []


def get_single_token_balance(
    walletAddress: str, chainName: str, tokenSymbolOrAddress: str
) -> float:
    """
    Calls the new Balances service to get the balance for a single token
    """
    try:
        params = {
            "walletAddress": walletAddress,
            "chainName": chainName,
            "tokenSymbolOrAddress": tokenSymbolOrAddress,
        }
        response = requests.get(
            f"{FIREBASE_SERVER_ENDPOINT}/getTokenBalanceFromBlockchain", params=params
        )
        response.raise_for_status()
        data = response.json()

        return data["token_balance"]
    except Exception as e:
        print(f"Error getting token balance: {e}")
        return 0


def update_balances_after_transaction(transaction_id: str):
    """
    Updates balances after a transaction is completed
    """
    try:
        payload = {"transactionId": transaction_id}
        response = requests.post(
            f"{FIREBASE_SERVER_ENDPOINT}/updateBalancesAfterTransaction", json=payload
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error updating balances after transaction: {e}")
        return None
