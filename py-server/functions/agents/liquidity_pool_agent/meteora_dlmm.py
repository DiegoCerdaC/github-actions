import requests
from typing import Annotated, Dict, List, Union, Any, Optional

BASE_URL = "https://dlmm-api.meteora.ag"

# use this one preferrably
def get_all_pairs_by_groups(page: Optional[int] = 0,
                            limit: Optional[int] = 50,
                            skip_size: Optional[int] = 0,
                            pools_to_top: Optional[List[str]] = None,
                            sort_key: Optional[str] = 'volume',
                            order_by: Optional[str] = 'desc',
                            search_term: Optional[str] = None,
                            include_unknown: Optional[bool] = True,
                            hide_low_tvl: Optional[float] = None,
                            hide_low_apr: Optional[bool] = None,
                            include_token_mints: Optional[List[str]] = None,
                            include_pool_token_pairs: Optional[List[str]] = None) -> Dict[str, Union[int, List[Dict[str, Any]]]]:
    """
    Retrieve all pairs grouped by specified criteria.

    :param page: Page number. Default is 0.
    :param limit: Number of items per page. Default is 50.
    :param skip_size: Number of items to skip. Default is 0.
    :param pools_to_top: Pools to be sorted to top.
    :param sort_key: Sort key. Default is Volume.
    :param order_by: Sort order. Default is Descending.
    :param search_term: Search term.
    :param include_unknown: Include pool with unverified token. Default true.
    :param hide_low_tvl: Toggle pools with lower TVL than the value passed in.
    :param hide_low_apr: Toggle pools with low APR.
    :param include_token_mints: Only include token mints. Allow list of token mints.
    :param include_pool_token_pairs: Only include pool token pairs. Allow list of pool token mints.
    :returns: Grouped pairs information.
    """
    params = {
        'page': page,
        'limit': limit,
        'skip_size': skip_size,
        'pools_to_top': pools_to_top,
        'sort_key': sort_key,
        'order_by': order_by,
        'search_term': search_term,
        'include_unknown': str(include_unknown).lower(),
        'hide_low_tvl': hide_low_tvl,
        'hide_low_apr': str(hide_low_apr).lower() if hide_low_apr is not None else None,
        'include_token_mints': include_token_mints,
        'include_pool_token_pairs': include_pool_token_pairs
    }
    params = {k: v for k, v in params.items() if v is not None}
    
    response = requests.get(f"{BASE_URL}/pair/all_by_groups", params=params)
    response.raise_for_status()
    return response.json()


def get_pair(pair_address: Annotated[str, 'Address of the liquidity pair']) -> Annotated[Dict[str, Union[str, float, int, bool]], 'Information about the liquidity pair. Keys: address, name, mint_x, mint_y, reserve_x, reserve_y, reserve_x_amount, reserve_y_amount, bin_step, base_fee_percentage, max_fee_percentage, protocol_fee_percentage, liquidity, reward_mint_x, reward_mint_y, fees_24h, today_fees, trade_volume_24h, cumulative_trade_volume, cumulative_fee_volume, current_price, apr, apy, farm_apr, farm_apy, hide']:
    """
    Retrieve information about a specific liquidity pair.

    :param pair_address: Address of the liquidity pair.
    :returns: Information about the liquidity pair.
    """
    response = requests.get(f"{BASE_URL}/pair/{pair_address}")
    response.raise_for_status()
    return response.json()

