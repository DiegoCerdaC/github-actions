from solders.pubkey import Pubkey
from web3 import Web3


def is_evm(wallet_address):
    try:
        is_evm_address = Web3.is_address(wallet_address)
        return is_evm_address
    except:
        return False


def is_solana(wallet_address):
    try:
        Pubkey.from_string(wallet_address)
        return True
    except Exception:
        return False
