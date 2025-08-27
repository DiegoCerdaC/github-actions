import requests
from config import FIREBASE_SERVER_ENDPOINT


def sign_transaction(transaction, type, action, sender_wallet_address, chain=None):
    """
    Sign a transaction using delegated action service
    
    Args:
        transaction: string (solana) or object (evm)
        type: string - EVM or SOLANA
        chain: string - any EVM Supported Chains (optional)
        action: string - signMessage or signTransaction
        sender_wallet_address: string - sender's wallet address. Needs to be Privy Embedded Wallet.
    
    Returns:
        string: transaction hash
    """
    try:
        payload = {
            "transaction": transaction,
            "type": type,
            "chain": chain,
            "action": action,
            "senderWalletAddress": sender_wallet_address,
            "fromClient": False
        }
        response = requests.post(f"{FIREBASE_SERVER_ENDPOINT}/signWithDelegatedAction", json=payload)
        response.raise_for_status()

        return response.json().get("hash", "")
    except requests.exceptions.RequestException as error:
        print(f"Error with signing transactions due to api request: {error}")
        raise # raise original error
    except Exception as error:
        print(f"Error with signing transactions: {error}")
        raise # raise original error
