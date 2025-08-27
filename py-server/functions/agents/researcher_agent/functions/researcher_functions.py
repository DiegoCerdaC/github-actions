import json, requests
from config import FIREBASE_SERVER_ENDPOINT, SERPER_API_KEY
from typing import List, Dict
from datetime import datetime, timedelta
from utils.firebase import (
    generate_firebase_id_token,
    get_request_ctx,
    save_agent_thought,
)
import pytz

from .coinmarketcap_functions import get_cryptocurrency_by_symbol
from .dexscreener_functions import (
    get_dexscreener_token_pair_info,
    get_dexscreener_token_pair_info_by_chain_and_token_address,
    is_possible_rug,
)
from agents.unified_transfer.transfer_functions import SOL_NATIVE_ADDRESS


serper_api_key = SERPER_API_KEY


if not serper_api_key:
    raise ValueError("Missing required API keys")


async def search_on_google(search_keywords_list: List[str]) -> List[Dict[str, str]]:
    """Search for keywords and return the results"""
    all_results = []

    for search_keywords in search_keywords_list:
        try:
            search_results = search(search_keywords)

            # Process the search results
            for entry in search_results.get("organic", [])[:5]:
                result_info = {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "snippet": entry.get("snippet", ""),
                    "position": entry.get("position", ""),
                    "source": "google_search",
                    "query": search_keywords,
                }
                all_results.append(result_info)

        except Exception as e:
            print(f"Error searching for '{search_keywords}': {str(e)}")
            continue
    return all_results


def search(search_keyword: str):
    """Search for a keyword using the Serper API"""
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": search_keyword})
    headers = {"X-API-KEY": serper_api_key, "Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    return json.loads(response.text)


async def get_additional_context(
    search_query: List[str], tasks: List[str]
) -> List[Dict[str, str]]:
    """
    Main function to get additional context through web search.
    Integrated version that works with the researcher agent directly.

    Args:
        search_query: List of search queries
        tasks: List of tasks to complete

    Returns:
        List[Dict[str, str]]: Processed results ready for the agent
    """
    try:
        search_results = await search_on_google(search_query)
        return search_results

    except Exception as e:
        print(f"Error in get_additional_context: {str(e)}")
        return []


# Portfolio functions
def get_portfolio_history(chat_id: str) -> dict:
    url = f"{FIREBASE_SERVER_ENDPOINT}/getPortfolioValueAndHistory"
    user_id = get_request_ctx(chat_id, "user_id")
    if not user_id:
        return {"error": "No user ID found in chat context"}

    try:
        id_token = generate_firebase_id_token(user_id)
    except Exception as e:
        print(f"Error generating Firebase token: {str(e)}")
        return {"error": "Failed to generate authentication token"}

    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            url, headers=headers, json={"fromServer": True, "userId": user_id}
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            return {"error": "No portfolio data returned"}
        return data
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch portfolio history: {e}"}


def format_portfolio_results(results: dict, detailed: bool = False) -> str:
    try:
        if "error" in results:
            return f"Error: {results['error']}"

        total_value = f"${results['total_value']}"
        changes = results.get("changes", {})
        token_insights = results.get("token_insights", [])
        allocation = results.get("allocation", {})

        if not detailed:
            response = f"Your portfolio is worth {total_value}.\n"

            # Add allocation summary
            if allocation:
                response += f"Portfolio allocation:\n"
                response += f"- {allocation['invested_percentage']:.1f}% invested (${allocation['invested_value']:.2f})\n"
                response += f"- {allocation['stable_percentage']:.1f}% in stablecoins (${allocation['stable_value']:.2f})\n\n"

            if "1d" in changes:
                ch = changes["1d"]
                response += (
                    f"Yesterday to today: {'+' if ch['usd'] >= 0 else ''}{ch['usd']} USD ({ch['pct']}%)"
                    + (" (approximated)" if not ch["has_exact_data"] else "")
                    + ".\n"
                )
            else:
                response += "No data from yesterday.\n"

            long_term = next((p for p in ["30d", "15d", "7d"] if p in changes), None)
            if long_term:
                ch = changes[long_term]
                days = long_term.replace("d", "")
                response += (
                    f"In {days} days: {'+' if ch['usd'] >= 0 else ''}{ch['usd']} USD ({ch['pct']}%)"
                    + (" (approximated)" if not ch["has_exact_data"] else "")
                    + ".\n"
                )
            if "all_time" in changes:
                ch = changes["all_time"]
                response += f"Total: {'+' if ch['usd'] >= 0 else ''}{ch['usd']} USD ({ch['pct']}%).\n"

            # Add token insights summary
            if token_insights:
                response += "\nTop Token Analysis:\n"
                for insight in token_insights:
                    symbol = insight["symbol"]
                    chain = insight["chain"]
                    value = insight["usd_value"]
                    perf = insight.get("performance", {})
                    warnings = insight.get("warnings", [])
                    is_stable = insight.get("is_stable", False)

                    response += f"- {symbol} (${value:.2f} on {chain}){' (Stablecoin)' if is_stable else ''}:\n"

                    # Add performance metrics if available and not a stablecoin
                    if not is_stable:
                        if "24h_price_change" in perf:
                            response += (
                                f"  24h change: {perf['24h_price_change']:.2f}%\n"
                            )
                        if "24h_volume" in perf:
                            # Handle volume formatting directly
                            volume = perf["24h_volume"]
                            if isinstance(volume, str):
                                response += f"  24h volume: {volume}\n"
                            else:
                                volume_in_k = float(volume)
                                if volume_in_k >= 1000 * 1000 * 1000:  # Trillions
                                    response += f"  24h volume: ${(volume_in_k / (1000 * 1000 * 1000)):.2f}T\n"
                                elif volume_in_k >= 1000 * 1000:  # Billions
                                    response += f"  24h volume: ${(volume_in_k / (1000 * 1000)):.2f}B\n"
                                elif volume_in_k >= 1000:  # Millions
                                    response += (
                                        f"  24h volume: ${(volume_in_k / 1000):.2f}M\n"
                                    )
                                else:  # Thousands
                                    response += f"  24h volume: ${volume_in_k:.2f}K\n"

                        # Add value change analysis
                        value_changes = []
                        if "price_change_7d" in perf:
                            value_changes.append(f"7d: {perf['price_change_7d']:.2f}%")
                        if "price_change_30d" in perf:
                            value_changes.append(
                                f"30d: {perf['price_change_30d']:.2f}%"
                            )
                        if value_changes:
                            response += f"  Price changes: {', '.join(value_changes)}\n"

                        # Add market analysis and suggestions
                        if "market_cap" in perf and perf["market_cap"] > 0:
                            market_cap = perf["market_cap"]
                            if market_cap >= 1000:  # Billions
                                response += (
                                    f"  Market cap: ${(market_cap / 1000):.2f}B\n"
                                )
                            else:  # Millions
                                response += f"  Market cap: ${market_cap:.2f}M\n"

                        # Add performance analysis and suggestions
                        analysis = []
                        suggestions = []

                        # Analyze short-term performance
                        if "24h_price_change" in perf:
                            if perf["24h_price_change"] > 5:
                                analysis.append("Strong upward momentum")
                                suggestions.append("Consider taking partial profits")
                            elif perf["24h_price_change"] < -5:
                                analysis.append("Significant price drop")
                                suggestions.append("Monitor closely for stabilization")

                        # Analyze volume
                        if "24h_volume" in perf and "market_cap" in perf:
                            market_cap = perf.get("market_cap", 0)
                            if (
                                market_cap > 0
                            ):  # Only calculate ratio if market cap is positive
                                volume = perf.get("24h_volume", 0)
                                if isinstance(volume, str):
                                    # Skip volume analysis for pre-formatted strings
                                    continue
                                volume_to_mcap = float(volume) / market_cap
                                if volume_to_mcap > 0.1:
                                    analysis.append("High trading activity")
                                elif volume_to_mcap < 0.01:
                                    analysis.append("Low liquidity")
                                    suggestions.append("Be cautious with large trades")

                        # Add trend analysis
                        if "price_change_7d" in perf and "price_change_30d" in perf:
                            short_term = perf["price_change_7d"]
                            long_term = perf["price_change_30d"]
                            if short_term > 0 and long_term > 0:
                                analysis.append("Bullish trend")
                            elif short_term < 0 and long_term < 0:
                                analysis.append("Bearish trend")
                                suggestions.append("Consider DCA strategy")
                            elif short_term > 0 and long_term < 0:
                                analysis.append("Potential trend reversal")

                        if analysis:
                            response += f"  Analysis: {', '.join(analysis)}\n"
                        if suggestions:
                            response += f"  Suggestions: {', '.join(suggestions)}\n"

                    # Add warnings if any
                    if warnings:
                        response += f"  ⚠️ {', '.join(warnings)}\n"
            return response

        else:
            response = f"Detailed analysis (Current value: {total_value}):\n"

            # Add detailed allocation information
            if allocation:
                response += "\nPortfolio Allocation:\n"
                response += f"Invested assets: ${allocation['invested_value']:.2f} ({allocation['invested_percentage']:.1f}%)\n"
                response += f"Stablecoins: ${allocation['stable_value']:.2f} ({allocation['stable_percentage']:.1f}%)\n"
                response += f"Total value: {total_value}\n\n"

            response += "Performance by Period:\n"
            for period, ch in changes.items():
                period_name = {
                    "1d": "24h",
                    "7d": "7 days",
                    "15d": "15 days",
                    "30d": "30 days",
                    "all_time": "Total",
                }[period]
                response += (
                    f"- {period_name}: {'+' if ch['usd'] >= 0 else ''}{ch['usd']} USD ({ch['pct']}%)"
                    + (" (approximated)" if not ch["has_exact_data"] else "")
                    + "\n"
                )

            # Add detailed token insights
            if token_insights:
                response += "\nDetailed Token Analysis:\n"
                for insight in token_insights:
                    symbol = insight["symbol"]
                    chain = insight["chain"]
                    value = insight["usd_value"]
                    perf = insight.get("performance", {})
                    warnings = insight.get("warnings", [])
                    is_stable = insight.get("is_stable", False)

                    response += f"\n{symbol} Analysis (${value:.2f} on {chain}){' (Stablecoin)' if is_stable else ''}:\n"

                    # Add all available performance metrics if not a stablecoin
                    if perf and not is_stable:
                        response += "Performance Metrics:\n"
                        if "24h_price_change" in perf:
                            response += (
                                f"- 24h price change: {perf['24h_price_change']:.2f}%\n"
                            )
                        if "24h_volume" in perf:
                            response += f"- 24h volume: {perf['24h_volume']}\n"
                        if "market_cap" in perf and perf["market_cap"] > 0:
                            response += f"- Market cap: {perf['market_cap']}\n"
                        if "price_change_7d" in perf:
                            response += (
                                f"- 7d price change: {perf['price_change_7d']:.2f}%\n"
                            )
                        if "price_change_30d" in perf:
                            response += (
                                f"- 30d price change: {perf['price_change_30d']:.2f}%\n"
                            )

                    # Add all warnings
                    if warnings:
                        response += "Warnings:\n"
                        for warning in warnings:
                            response += f"⚠️ {warning}\n"
            return response

    except Exception as e:
        print(f"Error in format_portfolio_results: {str(e)}")
        return f"Error formatting results: {str(e)}"


def analyze_portfolio_history(chat_id: str, detailed: bool = False) -> str:
    try:
        save_agent_thought(
            chat_id=chat_id,
            thought="Fetching portfolio data...",
        )

        user_id = get_request_ctx(chat_id, "user_id")
        if not user_id:
            return {"error": "No user ID found in chat context"}

        try:
            id_token = generate_firebase_id_token(user_id)
        except Exception as e:
            print(f"Error generating Firebase token: {str(e)}")
            return {"error": "Failed to generate authentication token"}

        headers = {
            "Authorization": f"Bearer {id_token}",
            "Content-Type": "application/json",
        }

        save_agent_thought(
            chat_id=chat_id,
            thought="Gathering balances...",
        )

        url = f"{FIREBASE_SERVER_ENDPOINT}/getBalances?skipCache=false"
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()

        if not data or "balances" not in data:
            return {"error": "No portfolio data returned"}

        # Define known stablecoins (case-insensitive)
        stablecoins = {
            "usdc",
            "usdt",
            "dai",
            "fdusd",
            "busd",
            "tusd",
            "usdp",
            "frax",
            "gusd",
            "lusd",
            "susd",
            "usdd",
            "mimatic",
            "cusd",
            "nusd",
            "usdh",
        }

        # Calculate portfolio allocation
        total_value = sum(
            float(token.get("usd_amount", 0)) for token in data["balances"]
        )
        stable_value = sum(
            float(token.get("usd_amount", 0))
            for token in data["balances"]
            if token["symbol"].lower() in stablecoins
        )
        invested_value = total_value - stable_value

        # Calculate percentages
        stable_percentage = (stable_value / total_value * 100) if total_value > 0 else 0
        invested_percentage = (
            (invested_value / total_value * 100) if total_value > 0 else 0
        )

        save_agent_thought(
            chat_id=chat_id,
            thought="Analyzing token performance...",
        )

        # Sort tokens by USD value to get top holdings
        sorted_balances = sorted(
            data["balances"], key=lambda x: float(x.get("usd_amount", 0)), reverse=True
        )

        # Get detailed analysis for top non-stablecoin tokens
        token_insights = []
        tokens_analyzed = 0
        for token in sorted_balances:
            # Skip stablecoins and very small balances
            if (
                token["symbol"].lower() in stablecoins
                or float(token.get("usd_amount", 0)) < 0.1
            ):
                continue

            # Stop after analyzing 3 non-stablecoin tokens
            if tokens_analyzed >= 3:
                break

            symbol = token["symbol"]
            chain = token["chain"]
            usd_amount = float(token["usd_amount"])

            insight = {
                "symbol": symbol,
                "chain": chain,
                "amount": token["amount"],
                "usd_value": usd_amount,
                "warnings": [],
                "performance": {},
                "is_stable": symbol.lower() in stablecoins,
            }

            try:
                # Get DexScreener data for trading analysis
                if chain == "SOLANA":
                    if token["address"] == SOL_NATIVE_ADDRESS:
                        save_agent_thought(
                            chat_id=chat_id,
                            thought="Fetching token pair info...",
                            isFinalThought=True,
                        )
                        pair_info = (
                            get_dexscreener_token_pair_info_by_chain_and_token_address(
                                chat_id,
                                chain,
                                token["address"],
                            )
                        )
                    else:
                        save_agent_thought(
                            chat_id=chat_id,
                            thought="Fetching token pair info...",
                            isFinalThought=True,
                        )
                        pair_info = get_dexscreener_token_pair_info(
                            chat_id, symbol, "USDC"
                        )

                    if isinstance(pair_info, dict):
                        # Add trading metrics
                        insight["performance"].update(
                            {
                                "24h_price_change": pair_info.get(
                                    "24_hrs_price_change", 0
                                ),
                                "24h_volume": pair_info.get("volume", 0),
                                "market_cap": pair_info.get("marketCap", 0),
                            }
                        )

                        # Check for potential risks
                        if (
                            pair_info.get("24_hrs_sells", 0)
                            > pair_info.get("24_hrs_buys", 0) * 2
                        ):
                            insight["warnings"].append("High sell pressure detected")

                        # Check if token might be risky
                        if is_possible_rug(token["address"]):
                            insight["warnings"].append("Token shows some risk signals")

                # Get CoinMarketCap data for additional insights
                try:
                    cmc_data = get_cryptocurrency_by_symbol(symbol, chat_id)

                    if cmc_data and isinstance(cmc_data, dict):
                        quote_data = cmc_data.get("quote", {})
                        # Get raw volume value before formatting
                        raw_volume = quote_data.get("volume_24h", 0)
                        insight["performance"].update(
                            {
                                "24h_price_change": quote_data.get(
                                    "percent_change_24h", 0
                                ),
                                "24h_volume": raw_volume,  # Pass the raw volume value
                                "market_cap": quote_data.get("market_cap", 0)
                                / 10**6,  # Convert to millions
                                "price_change_7d": quote_data.get(
                                    "percent_change_7d", 0
                                ),
                                "price_change_30d": quote_data.get(
                                    "percent_change_30d", 0
                                ),
                            }
                        )

                except Exception as e:
                    print(f"Error getting CMC data for {symbol}: {str(e)}")

            except Exception as e:
                print(f"Error analyzing token {symbol}: {str(e)}")
                continue

            token_insights.append(insight)
            tokens_analyzed += 1

        # From here on, the thoughts will be below all of the UIs rendered
        save_agent_thought(
            chat_id=chat_id,
            thought="Tracking portfolio history...",
        )

        portfolio_data = get_portfolio_history(chat_id)
        if "error" in portfolio_data:
            return portfolio_data["error"]

        # Continue with existing portfolio analysis
        utc = pytz.UTC
        now = datetime.now(utc)
        periods = {
            "1d": now - timedelta(days=1),
            "7d": now - timedelta(days=7),
            "15d": now - timedelta(days=15),
            "30d": now - timedelta(days=30),
        }

        current_total = sum(float(wallet["value_usd"]) for wallet in portfolio_data)

        results = {
            "total_value": round(current_total, 2),
            "changes": {},
            "wallets": [],
            "token_insights": token_insights,
            "allocation": {
                "stable_value": round(stable_value, 2),
                "stable_percentage": round(stable_percentage, 2),
                "invested_value": round(invested_value, 2),
                "invested_percentage": round(invested_percentage, 2),
            },
        }

        for wallet in portfolio_data:
            wallet_info = {
                "address": wallet["wallet_address"],
                "current_value": float(wallet["value_usd"]),
                "history": [],
            }
            if wallet.get("history"):
                history = sorted(
                    [
                        {
                            "date": datetime.fromisoformat(
                                h["date"].replace("Z", "+00:00")
                            ).replace(tzinfo=utc),
                            "value": float(h["value_usd"]),
                        }
                        for h in wallet["history"]
                    ],
                    key=lambda x: x["date"],
                    reverse=True,
                )
                wallet_info["history"] = history
            results["wallets"].append(wallet_info)

        save_agent_thought(
            chat_id=chat_id,
            thought="Calculating changes...",
        )

        for period_name, period_date in periods.items():
            period_total = 0
            has_data = False
            for wallet in results["wallets"]:
                for entry in wallet["history"]:
                    if entry["date"] <= period_date:
                        period_total += entry["value"]
                        has_data = True
                        break
            if has_data:
                change_usd = current_total - period_total
                change_pct = (
                    (change_usd / period_total) * 100 if period_total > 0 else 0
                )
                results["changes"][period_name] = {
                    "usd": round(change_usd, 2),
                    "pct": round(change_pct, 2),
                    "has_exact_data": (
                        period_date.date()
                        in [
                            h["date"].date()
                            for w in results["wallets"]
                            for h in w["history"]
                        ]
                    ),
                }

        earliest_total = 0
        has_early_data = False
        for wallet in results["wallets"]:
            if wallet["history"]:
                earliest_total += wallet["history"][-1]["value"]
                has_early_data = True
        if has_early_data:
            change_usd = current_total - earliest_total
            change_pct = (
                (change_usd / earliest_total) * 100 if earliest_total > 0 else 0
            )
            results["changes"]["all_time"] = {
                "usd": round(change_usd, 2),
                "pct": round(change_pct, 2),
                "has_exact_data": True,
            }

        result = format_portfolio_results(results, detailed)
        save_agent_thought(
            chat_id=chat_id,
            thought="Sending portfolio results...",
            isFinalThought=True,
        )
        return result
    except Exception as e:
        return f"Error analyzing portfolio: {str(e)}"
