from services.balances import get_wallet_balance, BalanceServiceType
from utils.firebase import get_top_traders_wallets
import random


def get_top_holdings_of_traders():
    """Get the top holdings of top selected traders wallets"""
    wallets_to_check = get_top_traders_wallets()

    # Pick 4 random wallets to avoid rate limits
    if len(wallets_to_check) >= 5:
        wallets_to_check = random.sample(wallets_to_check, 4)
    else:
        print("Not enough wallets to sample.")
        return []

    top_holdings = []
    for wallet in wallets_to_check:
        response = get_wallet_balance(wallet, BalanceServiceType.SOLANA.value)
        if response:
            response = [token for token in response if token["symbol"] != "SOL"]
            top_holdings.append(
                sorted(response, key=lambda x: x["usd_amount"], reverse=True)[:10]
            )

    return top_holdings
