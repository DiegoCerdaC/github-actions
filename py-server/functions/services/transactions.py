from enum import Enum
import requests
from config import FIREBASE_SERVER_ENDPOINT


class TransactionType(Enum):
    SWAP = "swap"
    BRIDGE = "bridge"
    TRANSFER = "transfer"
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    STAKE = "stake"
    UNSTAKE = "unstake"
    CLAIM_FEE = "claim fee"
    REQUEST_WITHDRAW = "request_withdraw"
    LIQUIDATION = "liquidation"


def save_transaction_to_db(transaction) -> dict:
    """
    Calls the ts-server saveTransactionOnDB endpoint to save on the db the transactions that are 100% handled on py-server

    Args:
       transaction: The transaction to save on the db (it should include all the needed params that the UI component needs)

    Returns:
        dict: The response from the service.
    """
    try:
        body = {
            "transactionData": transaction,
        }
        response = requests.post(
            f"{FIREBASE_SERVER_ENDPOINT}/saveTransactionOnDB", json=body
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"error": "Failed to call saveTransactionOnDB", "error_message": e}
