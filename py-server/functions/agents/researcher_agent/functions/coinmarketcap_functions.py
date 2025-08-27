import requests
from typing import Annotated, Dict, List, Optional, TypedDict, Any
from datetime import datetime, timedelta
from config import COINMARKETCAP_API_KEY
from utils.firebase import save_ui_message
from .common_functions import search_on_google
from utils.firebase import save_agent_thought


class QuoteInfo(TypedDict):
    price: float
    volume_24h: float
    volume_change_24h: float
    percent_change_1h: float
    percent_change_24h: float
    percent_change_7d: float
    percent_change_30d: float
    percent_change_60d: float
    percent_change_90d: float
    market_cap: float
    market_cap_dominance: float
    fully_diluted_market_cap: float
    tvl: Optional[float]
    last_updated: str


class PlatformInfo(TypedDict, total=False):
    id: int
    name: str
    symbol: str
    slug: str
    token_address: str


class CryptocurrencyInfo(TypedDict):
    id: int
    name: str
    symbol: str
    slug: str
    num_market_pairs: int
    date_added: str
    tags: List[str]
    max_supply: Optional[float]
    circulating_supply: float
    total_supply: float
    infinite_supply: bool
    platform: Optional[PlatformInfo]
    cmc_rank: int
    self_reported_circulating_supply: Optional[float]
    self_reported_market_cap: Optional[float]
    tvl_ratio: Optional[float]
    last_updated: str
    quote: Dict[str, QuoteInfo]  # Key of QuoteInfo is always "USD"


class UrlsInfo(TypedDict):
    website: List[str]
    technical_doc: List[str]
    twitter: List[str]
    reddit: List[str]
    message_board: List[str]
    announcement: List[str]
    chat: List[str]
    explorer: List[str]
    source_code: List[str]


class CryptocurrencyMetadataInfo(TypedDict):
    urls: UrlsInfo
    logo: str
    id: int
    name: str
    symbol: str
    slug: str
    description: str
    date_added: str
    date_launched: Optional[str]
    tags: List[str]
    platform: Optional[Dict[str, str]]
    category: str


class CryptocurrencyInfoWithMetadata(TypedDict):
    metadata: CryptocurrencyMetadataInfo
    data: CryptocurrencyInfo


coinmarketcap_headers = {
    "Accepts": "application/json",
    "X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY,
}
coinmarketcap_pro_base_url = "https://pro-api.coinmarketcap.com"


def get_cryptocurrency_by_id(
    id: Annotated[int, "The id of the cryptocurrency to get the info from."],
) -> CryptocurrencyMetadataInfo:
    """
    Returns the cryptocurrency by the given id from the CoinMarketCap API.

    # Parameters:
    - id (int): The id of the cryptocurrency to get the info from.

    # Returns:
    - str: A JSON-formatted response from the AI agent containing the cryptocurrency info.
    """
    coinmarketcap_url = f"{coinmarketcap_pro_base_url}/v2/cryptocurrency/info?id={id}"

    response = requests.get(coinmarketcap_url, headers=coinmarketcap_headers)
    coinmarketcap_data = response.json()["data"][str(id)]
    return coinmarketcap_data


def get_cryptocurrency_by_symbol(
    symbol: Annotated[str, "The symbol of the cryptocurrency to get the info from."],
    chat_id: Annotated[str, "The current chat id"],
) -> CryptocurrencyMetadataInfo:
    """
    Returns the cryptocurrency info by the given symbol from the CoinMarketCap API.

    # Parameters:
    - symbol (str): The symbol of the cryptocurrency to get the info from.
    - chat_id (str): The current chat id

    # Returns:
    - CryptocurrencyMetadataInfo: The cryptocurrency data including quotes or an error message
    """
    try:

        coinmarketcap_info_url = (
            f"{coinmarketcap_pro_base_url}/v2/cryptocurrency/info?symbol={symbol}"
        )
        coinmarketcap_quote_url = f"{coinmarketcap_pro_base_url}/v2/cryptocurrency/quotes/latest?symbol={symbol}"

        response_info = requests.get(
            coinmarketcap_info_url, headers=coinmarketcap_headers
        )
        coinmarketcap_info_data = response_info.json()["data"][symbol][0]

        response_quote = requests.get(
            coinmarketcap_quote_url, headers=coinmarketcap_headers
        )
        coinmarketcap_quote_data = response_quote.json()["data"][symbol][0]["quote"][
            "USD"
        ]

        coinmarketcap_info_data["quote"] = coinmarketcap_quote_data

        save_ui_message(
            chat_id=chat_id,
            renderData=coinmarketcap_info_data,
            component="currency_chart",
        )

        return coinmarketcap_info_data
    except Exception as e:
        print(f"Error in get_cryptocurrency_by_symbol: {str(e)}")
        return None


def get_highest_cryptocurrencies_gainers(
    time_frame: Annotated[
        str,
        "The time frame to get the cryptocurrencies  gainers from. Possible values: 1h, 24h, 7d",
    ] = "24h",
    num_results: Annotated[int, "The number of results to return. Default is 10"] = 10,
) -> List[CryptocurrencyInfo]:
    """
    Returns the list of cryptocurrencies by the given time frame from the CoinMarketCap API.
    Used to get trending and hot tokens if not category is specified

    # Prompts examples this function can handle
    - Which tokens are trending on SOLANA
    - Tell me the top 5 token gainers on SOLANA

    # Parameters:
    - time_frame (str): The time frame to get the cryptocurrencies gainers from. Possible values: 1h, 24h, 7d. Default is 24h
    - num_results (int): The number of results to return. Default is 10

    # Returns:
    - List[CryptocurrencyInfo]: A list of cryptocurrencies by the given time frame.
    """
    try:
        coinmarketcap_url = f"{coinmarketcap_pro_base_url}/v1/cryptocurrency/listings/latest?sort=percent_change_{time_frame}&limit={num_results}"

        response = requests.get(coinmarketcap_url, headers=coinmarketcap_headers)
        response.raise_for_status()
        coinmarketcap_data = response.json()["data"]
        return coinmarketcap_data[:num_results]
    except Exception as e:
        return f"There was an error fetching the crypto gainers: {str(e)}. Please try again later."


def get_cryptocurrencies_by_tags(
    chat_id: Annotated[str, "The current chat id"],
    tags: Annotated[
        List[str], "The ids of the categories/tags to filter the cryptocurrencies by."
    ],
    sort_by: Annotated[
        str,
        "The sorting criteria. Possible values: percent_change_1h, percent_change_24h, percent_change_7d, market_cap, volume_24h, volume_7d, volume_30d. Default is percent_change_24h",
    ] = "percent_change_24h",
    num_results: Annotated[int, "The number of results to return. Default is 10"] = 10,
    use_frontend_quoting: Annotated[
        bool, "Whether to use frontend quoting or not."
    ] = True,
) -> List[CryptocurrencyInfo]:
    """
    Returns the list of cryptocurrencies by the given tag or category.
    Used to get information about tokens that match the given tags/category specified by the user.

    Example prompts:
    - I want to know the trending RWA tokens on SOLANA
    - What are the trending memes on SOLANA
    - What AI tokens are trending right now
    - What gaming tokens are hot now

    # Parameters:
    - chat_id (str): The current chat id
    - tags (List[str]): The ids of the categories/tags to filter the cryptocurrencies by.
    - sort_by (str): The sorting criteria. Possible values: percent_change_1h, percent_change_24h, percent_change_7d, market_cap, volume_24h, volume_7d, volume_30d. Default is percent_change_24h
    - num_results (int): The number of results to return. Default is 10
    - should_show_ui (bool): Whether to show the UI or not. Default is False

    # Returns:
    - List[CryptocurrencyInfo]: A list of cryptocurrencies by the given tag.
    """
    aux = (
        "aux=volume_7d"
        if sort_by == "volume_7d"
        else "aux=volume_30d" if sort_by == "volume_30d" else ""
    )
    try:
        coinmarketcap_url = f"{coinmarketcap_pro_base_url}/v1/cryptocurrency/listings/latest?sort={sort_by}&limit=500&{aux}"

        response = requests.get(coinmarketcap_url, headers=coinmarketcap_headers)
        response.raise_for_status()
        coinmarketcap_data = response.json()["data"]
    except Exception as e:
        return f"There was an error fetching the cryptocurrencies: {str(e)}. Please try again later."

    coins = [
        coin
        for coin in coinmarketcap_data
        if all(
            any(
                user_tag.lower() in coin_tag.lower()
                for coin_tag in coin.get("tags", [])
            )
            for user_tag in tags
        )
    ]
    sorted_coins = sorted(coins, key=lambda x: x["quote"]["USD"][sort_by], reverse=True)
    limited_coins = sorted_coins[:num_results]
    if len(limited_coins) == 0:
        return "No cryptocurrencies found with the given tags"
    for coin in limited_coins:
        try:
            logo = coin.get("logo", None)
            if not logo:
                logo = get_cryptocurrency_by_id(coin["id"])["logo"]
            coin["logo"] = logo
        except Exception as e:
            print("Error getting logo", e)
    if use_frontend_quoting:
        save_ui_message(
            chat_id=chat_id,
            renderData=limited_coins,
            component="cryptocurrencies_performance",
        )
        return "Tokens fetched successfully"
    else:
        return limited_coins


async def get_comprehensive_market_data(
    chat_id: str, detailed_response: bool = False, use_frontend_quoting: bool = True
) -> Annotated[
    str,
    "Returns a comprehensive market overview including current status, 24h/week/month changes, and detailed historical data if requested.",
]:
    """
    Get comprehensive market data including both UI-friendly summary and text analysis.
    Use this to:
    - Fetch the latest market data
    - Generate a concise summary by default

    Use detailed_response=True when the user requests:
    - A detailed/long/comprehensive analysis
    - In-depth market insights
    - Full market report
    - Complete market overview
    Args:
        chat_id (str): The current chat id for saving UI messages
        detailed_response (bool): Whether to return a detailed response or a short summary
        use_frontend_quoting: (bool): Whether to use frontend quoting or not. Default is True.
    Returns:
        str: A string containing the summary or detailed analysis
    """
    try:
        save_agent_thought(
            chat_id=chat_id,
            thought="Fetching current market data...",
        )

        # Get crypto market data
        crypto_url = f"{coinmarketcap_pro_base_url}/v1/global-metrics/quotes/latest"
        crypto_response = requests.get(crypto_url, headers=coinmarketcap_headers)
        crypto_data = crypto_response.json()["data"]

        # Get Solana data
        solana_url = (
            f"{coinmarketcap_pro_base_url}/v2/cryptocurrency/quotes/latest?symbol=SOL"
        )
        solana_response = requests.get(solana_url, headers=coinmarketcap_headers)
        solana_data = solana_response.json()["data"]["SOL"][0]
        solana_dominance = (
            solana_data["quote"]["USD"]["market_cap"]
            / crypto_data["quote"]["USD"]["total_market_cap"]
        ) * 100

        current_mcap = crypto_data["quote"]["USD"]["total_market_cap"]
        current_volume = crypto_data["quote"]["USD"]["total_volume_24h"]
        current_btc_dom = crypto_data["btc_dominance"]
        current_eth_dom = crypto_data["eth_dominance"]

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Current market cap: ${current_mcap/1e12:.2f}T, 24h volume: ${current_volume/1e9:.2f}B",
        )

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Dominance: BTC: {current_btc_dom:.1f}% | ETH: {current_eth_dom:.1f}% | SOL: {solana_dominance:.1f}%",
        )

        # Get historical data for comparison
        historical_url = (
            f"{coinmarketcap_pro_base_url}/v1/global-metrics/quotes/historical"
        )
        now = datetime.now()
        params = {
            "time_start": (now - timedelta(days=30)).isoformat(),
            "time_end": now.isoformat(),
            "interval": "daily",
            "convert": "USD",
        }
        historical_response = requests.get(
            historical_url, headers=coinmarketcap_headers, params=params
        )
        historical_data = historical_response.json()["data"]["quotes"]

        save_agent_thought(
            chat_id=chat_id,
            thought="Calculating market volatility...",
        )

        # Calculate volatility
        volatility = 0.0
        if historical_data and len(historical_data) > 1:
            try:
                daily_changes = []
                for i in range(1, len(historical_data)):
                    prev_day = historical_data[i - 1]["quote"]["USD"][
                        "total_market_cap"
                    ]
                    curr_day = historical_data[i]["quote"]["USD"]["total_market_cap"]
                    if prev_day > 0:  # Prevent division by zero
                        daily_change = ((curr_day - prev_day) / prev_day) * 100
                        daily_changes.append(daily_change)

                if daily_changes:  # Only calculate if we have valid changes
                    mean = sum(daily_changes) / len(daily_changes)
                    volatility = (
                        sum((x - mean) ** 2 for x in daily_changes) / len(daily_changes)
                    ) ** 0.5
            except (KeyError, IndexError, ZeroDivisionError) as e:
                print(f"Error calculating volatility: {str(e)}")
                volatility = 0.0

        save_agent_thought(
            chat_id=chat_id,
            thought=f"30-day market volatility: {volatility:.1f}%",
        )

        save_agent_thought(
            chat_id=chat_id,
            thought="Gathering market insights from web...",
        )

        # Get market insights from web search
        search_queries = [
            "current stock market summary S&P 500 NASDAQ DOW",
            "crypto market summary bitcoin ethereum",
            "market overview today stocks crypto",
        ]
        web_summaries = await search_on_google(search_queries)
        market_insights = []

        for result in web_summaries:
            if any(
                keyword in result["title"].lower()
                for keyword in ["market", "stocks", "crypto", "bitcoin", "ethereum"]
            ):
                market_insights.append(
                    {
                        "title": result["title"],
                        "source": result["link"],
                        "summary": result["snippet"],
                    }
                )

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Found {len(market_insights)} relevant market insights",
        )

        save_agent_thought(
            chat_id=chat_id,
            thought="Analyzing market trends...",
        )

        mcap_24h_change = crypto_data["quote"]["USD"][
            "total_market_cap_yesterday_percentage_change"
        ]
        volume_24h_change = crypto_data["quote"]["USD"][
            "total_volume_24h_yesterday_percentage_change"
        ]

        save_agent_thought(
            chat_id=chat_id,
            thought=f"24h market cap change: {mcap_24h_change:+.1f}%, volume change: {volume_24h_change:+.1f}%",
        )

        # Structure the UI market summary
        market_summary_ui = {
            "crypto_market": {
                "total_market_cap": current_mcap,
                "total_volume_24h": current_volume,
                "btc_dominance": current_btc_dom,
                "eth_dominance": current_eth_dom,
                "sol_dominance": solana_dominance,
                "sol_price": solana_data["quote"]["USD"]["price"],
                "sol_volume_24h": solana_data["quote"]["USD"]["volume_24h"],
                "sol_percent_change_24h": solana_data["quote"]["USD"][
                    "percent_change_24h"
                ],
                "market_cap_change_24h": mcap_24h_change,
                "volume_change_24h": volume_24h_change,
                "active_cryptocurrencies": crypto_data["active_cryptocurrencies"],
                "volatility_30d": volatility,
                "historical_comparison": {
                    "week_ago": {
                        "market_cap": (
                            historical_data[-7]["quote"]["USD"]["total_market_cap"]
                            if len(historical_data) >= 7
                            else None
                        ),
                        "volume": (
                            historical_data[-7]["quote"]["USD"]["total_volume_24h"]
                            if len(historical_data) >= 7
                            else None
                        ),
                        "btc_dominance": (
                            historical_data[-7]["btc_dominance"]
                            if len(historical_data) >= 7
                            else None
                        ),
                    },
                    "two_weeks_ago": {
                        "market_cap": (
                            historical_data[-14]["quote"]["USD"]["total_market_cap"]
                            if len(historical_data) >= 14
                            else None
                        ),
                        "volume": (
                            historical_data[-14]["quote"]["USD"]["total_volume_24h"]
                            if len(historical_data) >= 14
                            else None
                        ),
                        "btc_dominance": (
                            historical_data[-14]["btc_dominance"]
                            if len(historical_data) >= 14
                            else None
                        ),
                    },
                    "month_ago": {
                        "market_cap": (
                            historical_data[0]["quote"]["USD"]["total_market_cap"]
                            if len(historical_data) > 0
                            else None
                        ),
                        "volume": (
                            historical_data[0]["quote"]["USD"]["total_volume_24h"]
                            if len(historical_data) > 0
                            else None
                        ),
                        "btc_dominance": (
                            historical_data[0]["btc_dominance"]
                            if len(historical_data) > 0
                            else None
                        ),
                    },
                },
            },
            "market_insights": market_insights[:3],  # Limit to top 3 insights
        }

        # Calculate weekly and monthly changes
        week_ago = historical_data[-7] if len(historical_data) >= 7 else None
        month_ago = historical_data[0] if len(historical_data) > 0 else None

        week_change = (
            (
                (current_mcap - week_ago["quote"]["USD"]["total_market_cap"])
                / week_ago["quote"]["USD"]["total_market_cap"]
                * 100
            )
            if week_ago
            else 0
        )
        month_change = (
            (
                (current_mcap - month_ago["quote"]["USD"]["total_market_cap"])
                / month_ago["quote"]["USD"]["total_market_cap"]
                * 100
            )
            if month_ago
            else 0
        )

        save_agent_thought(
            chat_id=chat_id,
            thought=f"Weekly change: {week_change:+.1f}%, Monthly change: {month_change:+.1f}%",
        )

        save_agent_thought(
            chat_id=chat_id,
            thought="Generating market analysis...",
        )

        summary = None
        # Generate short summary (default)
        if not detailed_response:
            short_summary = [
                f"The crypto market is valued at ${current_mcap/1e12:.2f}T, {'up' if mcap_24h_change > 0 else 'down'} {abs(mcap_24h_change):.1f}% in 24h.",
                f"BTC dominance: {current_btc_dom:.1f}%, ETH: {current_eth_dom:.1f}%, SOL: {solana_dominance:.1f}%.",
                f"Volume {'increased' if volume_24h_change > 0 else 'decreased'} by {abs(volume_24h_change):.1f}%.",
            ]
            summary = " ".join(short_summary)
        else:
            # Generate detailed analysis
            detailed_analysis = [
                f"The crypto market is currently valued at ${current_mcap/1e12:.2f}T, with a 24h volume of ${current_volume/1e9:.2f}B.",
                f"Bitcoin dominance stands at {current_btc_dom:.1f}%, while Ethereum holds {current_eth_dom:.1f}% and Solana at {solana_dominance:.1f}% of the market.",
                f"Solana is trading at ${solana_data['quote']['USD']['price']:.2f}, with a 24h change of {solana_data['quote']['USD']['percent_change_24h']:.1f}% and volume of ${solana_data['quote']['USD']['volume_24h']/1e9:.2f}B.",
                f"Over the last 24 hours, the market cap has {'increased' if mcap_24h_change > 0 else 'decreased'} by {abs(mcap_24h_change):.1f}%, with trading volume {'up' if volume_24h_change > 0 else 'down'} {abs(volume_24h_change):.1f}%.",
                f"Looking at the past week, the market has {'grown' if week_change > 0 else 'contracted'} by {abs(week_change):.1f}%.",
                f"On a monthly basis, the market shows a {'positive' if month_change > 0 else 'negative'} trend with a {abs(month_change):.1f}% change.",
                f"Market volatility over the past month has been {volatility:.1f}%, indicating {'high' if volatility > 5 else 'moderate' if volatility > 2 else 'low'} price fluctuations.",
            ]

            # Add market sentiment and trend analysis
            if mcap_24h_change > 2 and volume_24h_change > 10:
                detailed_analysis.append(
                    "The market is showing strong bullish momentum with significant volume increases."
                )
            elif mcap_24h_change < -2 and volume_24h_change > 10:
                detailed_analysis.append(
                    "The market is experiencing heightened selling pressure with increased trading activity."
                )
            else:
                detailed_analysis.append(
                    "The market is currently in a relatively stable phase with moderate trading activity."
                )

            # Add trend analysis
            if week_change > 5 and month_change > 10:
                detailed_analysis.append(
                    "The market is in a strong uptrend, showing consistent growth over both short and medium terms."
                )
            elif week_change < -5 and month_change < -10:
                detailed_analysis.append(
                    "The market is in a significant downtrend, with sustained losses across all timeframes."
                )
            elif abs(week_change) < 2 and abs(month_change) < 5:
                detailed_analysis.append(
                    "The market is showing signs of consolidation, with relatively stable prices across timeframes."
                )

            # Add market structure analysis
            if current_btc_dom > 50:
                detailed_analysis.append(
                    "Bitcoin continues to maintain strong market dominance, indicating a risk-off sentiment in the market."
                )
            elif current_btc_dom < 40:
                detailed_analysis.append(
                    "Altcoins are gaining market share, suggesting increased risk appetite among investors."
                )

            summary = " ".join(detailed_analysis)

        if use_frontend_quoting:
            # Save UI message
            save_ui_message(
                chat_id=chat_id,
                component="market_summary",
                renderData=market_summary_ui,
                thought="Task completed successfully",
                isFinalThought=True,
            )

        return summary

    except Exception as e:
        save_agent_thought(
            chat_id=chat_id,
            thought="Error generating market analysis.",
            isFinalThought=True,
        )
        return "Unable to generate market analysis at this time."
