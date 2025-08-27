import requests
from utils.firebase import save_agent_thought, save_ui_message

BASE_URL = "https://api.llama.fi"
YIELDS_URL = "https://yields.llama.fi/pools"


def get_top_protocols_by_chain_on_defi_llama(chain: str, chat_id: str, limit: int = 10):
    """
    List the top protocols by TVL for a given chain using DeFiLlama

    Args:
        chain (str): The chain to get the top protocols for.
        chat_id (str): The current chat id.
        limit (int): The number of protocols to return. Default is 10.

    Returns:
        list: A list of dictionaries containing the protocol info (name, tvl, url, description, category, logo).
    """
    try:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Fetching TOP {limit} protocols on {chain}...",
        )
        response = requests.get(f"{BASE_URL}/protocols")
        response.raise_for_status()
        protocols = response.json()
        limit = min(limit, 10)
        top_protocols = sorted(
            (
                protocol
                for protocol in protocols
                if chain.lower() in map(str.lower, protocol["chains"])
            ),
            key=lambda x: x["tvl"],
            reverse=True,
        )[:limit]

        data_to_display = [
            {
                "name": protocol["name"],
                "tvl": protocol["tvl"],
                "url": protocol["url"],
                "description": protocol["description"],
                "category": protocol["category"],
                "logo": protocol["logo"],
            }
            for protocol in top_protocols
        ]

        if len(data_to_display) > 0:
            save_ui_message(
                chat_id=chat_id,
                renderData=data_to_display,
                component="defi_llama_information",
            )
            return [protocol["name"] for protocol in data_to_display]
        else:
            return f"No protocols found on {chain}."
    except Exception as e:
        return (
            "There was an error fetching the top protocols by chain, try again later."
        )


def get_top_chains_by_tvl_on_defi_llama(chat_id: str, limit: int = 10):
    """
    Get the top chains by TVL using DeFiLlama

    Args:
        chat_id (str): The current chat id.
        limit (int): The number of chains to return. Default is 10.

    Returns:
        list: A list of dictionaries containing the chain info (name and tvl) ordered by tvl.
    """
    try:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Fetching TOP {limit} chains by TVL...",
        )
        response = requests.get(f"{BASE_URL}/v2/chains")
        response.raise_for_status()
        limit = min(limit, 10)
        data = sorted(
            ({"name": chain["name"], "tvl": chain["tvl"]} for chain in response.json()),
            key=lambda x: x["tvl"],
            reverse=True,
        )[:limit]

        if len(data) > 0:
            return f"Top {limit} chains and TVLs are: {data}"
        else:
            return f"Could not find any chains by TVL on DeFiLlama."
    except Exception as e:
        return "There was an error fetching the top chains by TVL, try again later."


def get_top_dexs_by_chain_on_defi_llama(chain: str, chat_id: str, limit: int = 10):
    """
    Get the top DEXs by volume for a given chain using DeFiLlama

    Args:
        chain (str): The chain to get the top DEXs for.
        chat_id (str): The current chat id.
        limit (int): The number of DEXs to return. Default is 10.

    Returns:
        list: A list of dictionaries containing the DEX info (name, tvl, url, description, category, logo).
    """
    try:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Fetching TOP {limit} DEXs on {chain}...",
        )
        response = requests.get(
            f"{BASE_URL}/overview/dexs?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true"
        )
        response.raise_for_status()
        response = response.json()
        protocols = response["protocols"]
        limit = min(limit, 10)
        top_dexs = sorted(
            (
                protocol
                for protocol in protocols
                if chain.lower() in map(str.lower, protocol.get("chains", []))
                and "total7d" in protocol
            ),
            key=lambda x: x["total7d"],
            reverse=True,
        )[:limit]
        data_to_display = [
            {
                "name": protocol["name"],
                "logo": protocol["logo"],
                "total24h": protocol["total24h"],
                "total7d": protocol["total7d"],
                "total30d": protocol["total30d"],
            }
            for protocol in top_dexs
        ]

        if len(data_to_display) > 0:
            save_ui_message(
                chat_id=chat_id,
                renderData=data_to_display,
                component="defi_llama_information",
            )
            return [protocol["name"] for protocol in data_to_display]
        else:
            return f"Could not find any DEXs on {chain}."

    except Exception as e:
        return "There was an error fetching the top DEXs by chain, try again later."


def get_top_yields_pools_by_chain_on_defi_llama(
    chain: str, chat_id: str, limit: int = 10
):
    """
    Get the top yields pools by volume for a given chain using DeFiLlama

    Args:
        chain (str): The chain to get the top yields pools for.
        chat_id (str): The current chat id.
        limit (int): The number of yields pools to return. Default is 10.

    Returns:
        list: A list of dictionaries containing the yields pool info (name, tvl, url, description, category, logo).
    """
    try:
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Fetching TOP {limit} pools on {chain}...",
        )
        response = requests.get(f"{YIELDS_URL}")
        response.raise_for_status()
        limit = min(limit, 10)
        response = response.json()
        pools = response["data"]
        chain_pools = [
            pool
            for pool in pools
            if pool["chain"].lower() == chain.lower()
            and pool["apyPct1D"] is not None
            and pool["tvlUsd"] > 100000
        ]

        top_pools = sorted(
            (pool for pool in chain_pools),
            key=lambda x: x["apyPct1D"],
            reverse=True,
        )[:limit]
        data_to_display = [
            {
                "project": pool["project"],
                "symbol": pool["symbol"],
                "tvlUsd": pool["tvlUsd"],
                "apyPct1D": pool["apyPct1D"],
                "apyPct7D": pool["apyPct7D"],
                "apyPct30D": pool["apyPct30D"],
                "ilRisk": pool["ilRisk"],
            }
            for pool in top_pools
        ]

        if len(data_to_display) > 0:
            save_ui_message(
                chat_id=chat_id,
                renderData=data_to_display,
                component="defi_llama_information",
            )
            return [
                {"project": pool["project"], "symbol": pool["symbol"]}
                for pool in data_to_display
            ]
        else:
            return f"Could not find any pools on {chain}."
    except Exception as e:
        return "There was an error fetching the top yields pools by chain, try again later."
