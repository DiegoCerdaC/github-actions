import pandas as pd
import json
from datetime import datetime, timedelta
from typing import List, Annotated
import requests
from agents.researcher_agent.functions import (
    CryptocurrencyInfo,
    coinmarketcap_headers,
    coinmarketcap_pro_base_url,
)
from utils.firebase import save_agent_thought


def get_cryptocurrencies_by_tags(
    tags: Annotated[
        List[str], "The ids of the categories/tags to filter the cryptocurrencies by."
    ] = ["memes", "solana-ecosystem"],
    sort_by: Annotated[
        str,
        "The sorting criteria. Possible values: percent_change_1h, percent_change_24h, percent_change_7d, market_cap, volume_24h, volume_7d, volume_30d. Default is percent_change_24h",
    ] = "percent_change_24h",
    num_results: Annotated[int, "The number of results to return. Default is 10"] = 10,
) -> List[CryptocurrencyInfo]:
    """
    Returns the list of cryptocurrencies by the given tag.
    Possible sort_by values: percent_change_1h, percent_change_24h, percent_change_7d, market_cap, volume_24h, volume_7d, volume_30d
    """
    aux = (
        "aux=volume_24h"
        if sort_by == "volume_24h"
        else "aux=volume_30d" if sort_by == "volume_30d" else ""
    )
    coinmarketcap_url = f"{coinmarketcap_pro_base_url}/v1/cryptocurrency/listings/latest?sort={sort_by}&limit=500&{aux}"

    response = requests.get(coinmarketcap_url, headers=coinmarketcap_headers)

    coinmarketcap_data = response.json()["data"]
    coins = [
        coin for coin in coinmarketcap_data if all(tag in coin["tags"] for tag in tags)
    ]

    sorted_coins = sorted(coins, key=lambda x: x["quote"]["USD"][sort_by], reverse=True)
    coins_info = []

    # Iterate through sorted coins and check for required properties
    for coin in sorted_coins:
        try:
            coin_info = {
                "coinmarketcap_id": coin["id"],
                "name": coin["name"],
                "symbol": coin["symbol"],
                "price": coin["quote"]["USD"]["price"],
                "chain": coin["platform"]["name"],
                "token_address": coin["platform"]["token_address"],
                "volume_24h": coin["quote"]["USD"]["volume_24h"],
                "percent_change_24h": coin["quote"]["USD"]["percent_change_24h"],
            }
            coins_info.append(coin_info)

            # Stop once we have enough results
            if len(coins_info) >= num_results:
                break

        except (KeyError, TypeError) as e:
            print(f"Error processing coin {coin.get('name', 'unknown')}: {e}")
            continue

    return coins_info[:num_results]

def get_top_3_memes(chat_id: Annotated[str, "The current chat id"]):
    """
    Gets the top 3 meme tokens on Solana blockchain recommended for buying based on a conservative trading strategy.
    # Parameters:
    - chat_id (str): the current chat id

    # Returns:
    - The top 3 trending meme tokens on Solana blockchain filtered by RSI, SMA, and EMA indicators.
    """
    save_agent_thought(
        chat_id=chat_id,
        thought="Fetching top trending meme tokens on Solana...",
    )

    # Get top 10 trending memes on Solana first
    top_10_memes = get_cryptocurrencies_by_tags(
        tags=["memes", "solana-ecosystem"],
        sort_by="percent_change_24h",
        num_results=10,
    )

    save_agent_thought(
        chat_id=chat_id,
        thought=f"Analyzing {len(top_10_memes)} meme tokens for trading opportunities...",
    )

    save_agent_thought(
        chat_id=chat_id,
        thought=f"Calculating technical indicators for discovered tokens...",
    )

    # Calculate indicators for each token
    for token in top_10_memes:
        token["price_chart"] = get_24h_prices_history(token["coinmarketcap_id"])
        if not token["price_chart"]:  # If no valid data, mark for exclusion later
            token["score"] = -1
            continue
        token["rsi"] = calculate_rsi(token["price_chart"])
        token["sma"] = calculate_sma(token["price_chart"])
        token["ema"] = calculate_ema(token["price_chart"])

        # Calculate score based on strategies for each token
        score = 0

        # RSI Strategy
        if token["rsi"] < 35:
            score += 2  # Cautious buy opportunity
        elif 35 <= token["rsi"] <= 60:
            score += 1  # Stable, no aggressive movements
        elif token["rsi"] > 65:
            score += 0  # Risk of overbought

        # SMA vs EMA Strategy
        if token["sma"] > token["ema"]:
            score += 1  # Long-term stability

        # SMA Strategy
        if token["sma"] < 30:
            score += 2  # Potentially undervalued
        elif 30 <= token["sma"] <= 70:
            score += 1  # Neutral

        # EMA Strategy
        if token["ema"] < 30:
            score += 2  # Potentially undervalued
        elif 30 <= token["ema"] <= 70:
            score += 1  # Neutral

        token["score"] = score

    # Filter valid tokens (discard tokens without price_chart)
    valid_tokens = [token for token in top_10_memes if token["score"] >= 0]

    # Sort by score (descending) and use percent_change_24h as tiebreaker
    sorted_tokens = sorted(
        valid_tokens,
        key=lambda x: (x["score"], x.get("percent_change_24h", 0)),
        reverse=True,
    )
    # Select the 3 best tokens
    top_3_memes = sorted_tokens[:3]

    save_agent_thought(
        chat_id=chat_id,
        thought="Generating trading recommendations...",
    )

    return top_3_memes


def get_24h_prices_history(token_id):
    try:

        base_url = (
            "https://pro-api.coinmarketcap.com/v3/cryptocurrency/quotes/historical"
        )

        now = datetime.now()
        one_day_ago = now - timedelta(hours=24)

        params = {
            "id": token_id,
            "convert": "USD",
            "time_start": one_day_ago.isoformat(),
            "time_end": now.isoformat(),
            "interval": "hourly",
        }

        response = requests.get(
            base_url, headers=coinmarketcap_headers, params=params
        ).json()

        prices_list = []

        if "data" in response and str(token_id) in response["data"]:
            quotes = response["data"][str(token_id)].get("quotes", [])

            if not quotes:
                return []

            for quote in quotes:
                prices_list.append(
                    {
                        "timestamp": quote["timestamp"],
                        "price": quote["quote"]["USD"]["price"],
                    }
                )
        else:
            print(f"No data found for token {token_id}")
            return []

        return prices_list

    except Exception as e:
        print("Error getting historic prices", e)
        return []


def calculate_rsi(price_chart, period=14):
    """
    Calculate the Relative Strength Index (RSI) for a given token.

    :param price_chart: List of price objects with keys "timestamp" and "price".
    :param period: The period for RSI calculation, default is 14.
    :return: The RSI value as a float.
    """
    # Extract the prices into a list
    prices = [entry["price"] for entry in price_chart]

    # Calculate price changes
    price_changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

    # Separate gains and losses
    gains = [max(0, change) for change in price_changes]
    losses = [abs(min(0, change)) for change in price_changes]

    # Create rolling averages for gains and losses using pandas
    gains_series = pd.Series(gains)
    losses_series = pd.Series(losses)

    avg_gain = gains_series.rolling(window=period, min_periods=period).mean()
    avg_loss = losses_series.rolling(window=period, min_periods=period).mean()

    # Calculate the Relative Strength (RS)
    rs = avg_gain / avg_loss

    # Calculate the RSI
    rsi = 100 - (100 / (1 + rs))

    # Return the last RSI value (most recent calculation)
    return rsi.iloc[-1]


def calculate_sma(price_chart, period=14):
    """
    Calculate the Simple Moving Average (SMA) for a given token.

    :param price_chart: List of price objects with keys "timestamp" and "price".
    :param period: The period for SMA calculation, default is 14.
    :return: The SMA value as a float.
    """
    # Extract the prices into a list
    prices = [entry["price"] for entry in price_chart]

    # Create a pandas Series from the list of prices
    prices_series = pd.Series(prices)

    # Calculate the SMA (rolling mean)
    sma = prices_series.rolling(window=period).mean()

    # Return the last SMA value (most recent calculation)
    return sma.iloc[-1]  # Most recent value of the SMA


def calculate_ema(price_chart, period=14):
    """
    Calculate the Exponential Moving Average (EMA) for a given token.

    :param price_chart: List of price objects with keys "timestamp" and "price".
    :param period: The period for EMA calculation, default is 14.
    :return: The EMA value as a float.
    """
    # Extract the prices into a list
    prices = [entry["price"] for entry in price_chart]

    # Create a pandas Series from the list of prices
    prices_series = pd.Series(prices)

    # Calculate the EMA (exponential moving average)
    ema = prices_series.ewm(span=period, adjust=False).mean()

    # Return the last EMA value (most recent calculation)
    return ema.iloc[-1]  # Most recent value of the EMA
