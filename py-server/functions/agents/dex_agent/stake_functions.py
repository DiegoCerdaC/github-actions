import requests
from config import SOL_VALIDATORS_API_KEY
from services.balances import get_wallet_balance, BalanceServiceType
from services.tokens import tokens_service
from agents.dex_agent.jupiter_functions import jupiter_get_quotes

supported_pools_and_tickers = {
    "Marinade": "msol",
    "Jpool": "jsol",
    "BlazeStake": "bsol",
    "Jito": "jitosol",
    "Edgevana": "edgesol",
    "Jupiter": "jupSol",
    "Lido": "stsol",
    "Infinity": "INF",
    "Drift": "dSOL",
    "Helius": "hSOL",
    "Binance": "BNSOL",
    "Bybit": "bbSOL",
}


# used in conservative agent, sol stake agent
def get_user_staked_balances(wallet_address: str):
    """
    Gets the user's staked balances in staked pools on Solana.
    Only use this when user wants to know their staked balances.

    # Parameters:
    - wallet_address (str): The address of the user's wallet

    # Returns:
    - The user's staked balances or an error message if an issue occurs
    """
    try:
        user_balances = {}
        user_solana_balances = get_wallet_balance(
            wallet_address, BalanceServiceType.SOLANA.value
        )
        pools_information = get_stake_pools_information()
        for pool in supported_pools_and_tickers:
            token_symbol = supported_pools_and_tickers[pool]
            token_info = tokens_service.get_token_metadata(
                token=token_symbol, chain="SOLANA"
            )
            if token_info is None:
                continue

            balance = next(
                (
                    b["amount"]
                    for b in user_solana_balances
                    if b["address"] == token_info["address"]
                ),
                0,
            )

            if balance > 0:
                for pool_info in pools_information:
                    if pool_info["ticker"] == supported_pools_and_tickers[pool]:
                        user_balances[pool] = {
                            "balance": balance,
                            "apy": pool_info["average_apy"],
                            "token_symbol": supported_pools_and_tickers[pool],
                        }

        if not user_balances:
            return "User doesn't have staked values"
        return user_balances
    except Exception as e:
        raise Exception(f"There was an error getting your staked balances: {e}.")


# used internally, for earnigns_for_users.py
def get_stake_pools_information():
    """
    Gets the information of the stake pools

    # Parameters:
    - None

    # Returns:
    - The list of stake pools
    """
    try:
        url = "https://www.validators.app/api/v1/stake-pools/mainnet"
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9,es-ES;q=0.8,es;q=0.7",
            "authorization": SOL_VALIDATORS_API_KEY,
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        if response.json()["stake_pools"] == []:
            raise Exception(
                "There was an error while obtaining the staking pools. Please try again in a few minutes."
            )

        pools = []
        for pool in response.json()["stake_pools"]:
            if pool["name"] in [
                "Marinade",
                "Jito",
                "BlazeStake",
                "Edgevana",
                "Jpool",
                "Lido",
            ]:
                pools.append(
                    {
                        "name": pool["name"],
                        "ticker": pool["ticker"],
                        "average_apy": pool["average_apy"],
                    }
                )

        # Add additional tokens that are not on the validators.app list
        additional_tokens = ["JupSOL", "INF", "dSOL", "hSOL", "BNSOL", "bbSOL"]
        url = "https://extra-api.sanctum.so/v1/apy/latest?" + "&".join(
            [f"lst={token}" for token in additional_tokens]
        )
        response = requests.get(url)
        response.raise_for_status()
        apys = response.json()["apys"]

        for token in additional_tokens:
            if token in apys:
                pool_name = next(
                    (
                        name
                        for name, ticker in supported_pools_and_tickers.items()
                        if ticker.lower() == token.lower()
                    ),
                    None,
                )
                if pool_name:
                    pools.append(
                        {
                            "name": pool_name,
                            "ticker": token,
                            "average_apy": apys[token] * 100,
                        }
                    )

        return pools
    except Exception as e:
        raise Exception(f"There was an error getting the stake pools information: {e}.")


# used in solana stake agent, conservative agent
def get_pool_with_highest_apy():
    """
    This function gets information of the stake pools that has the highest APY

    # Parameters:
    - None

    # Returns:
    - The pool with the highest APY
    """
    pools_information = get_stake_pools_information()
    return max(pools_information, key=lambda x: x["average_apy"])
