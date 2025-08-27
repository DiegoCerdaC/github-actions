import json, requests
from config import SERPER_API_KEY
from typing import List, Dict, Optional
from datetime import datetime, timezone

serper_api_key = SERPER_API_KEY

if not serper_api_key:
    raise ValueError("Missing required API keys")

from enum import Enum


class Timeframe(Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

    @classmethod
    def get_default(cls):
        return cls.DAY


# Map Timeframe enum to Serper API tbs values
tbs_map = {
    Timeframe.HOUR.value: "qdr:h",
    Timeframe.DAY.value: "qdr:d",
    Timeframe.WEEK.value: "qdr:w",
    Timeframe.MONTH.value: "qdr:m",
    Timeframe.YEAR.value: "qdr:y",
}


def search(search_keyword: str, timeframe: Optional[str]):
    """Search for a keyword using Serper API, with timeframe support"""
    url = "https://google.serper.dev/search"
    # Validate and normalize timeframe
    tbs_value = None
    if timeframe:
        tf = timeframe.lower()
        tbs_value = tbs_map.get(tf)

    payload_dict = {"q": search_keyword}
    if tbs_value:
        payload_dict["tbs"] = tbs_value

    payload = json.dumps(payload_dict)
    headers = {
        "X-API-KEY": serper_api_key,
        "Content-Type": "application/json",
    }
    response = requests.post(url, headers=headers, data=payload)
    return response.json()


async def search_on_google(
    search_keywords_list: List[str], timeframe: Optional[str] = None
) -> List[Dict[str, str]]:
    """Search for keywords and return the results
    timeframe can be `hour`, `day`, `week`, `month`, and `year`. By default, it is always None unless specified.
    """
    all_results = []

    for search_keywords in search_keywords_list:
        try:
            search_results = search(search_keywords, timeframe=timeframe)

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


def _parse_snippets(results: dict) -> List[str]:
    snippets = []
    if results.get("answerBox"):
        answer_box = results.get("answerBox", {})
        if answer_box.get("answer"):
            return [answer_box.get("answer")]
        elif answer_box.get("snippet"):
            return [answer_box.get("snippet").replace("\n", " ")]
        elif answer_box.get("snippetHighlighted"):
            return answer_box.get("snippetHighlighted")

    if results.get("knowledgeGraph"):
        kg = results.get("knowledgeGraph", {})
        title = kg.get("title")
        entity_type = kg.get("type")
        if entity_type:
            snippets.append(f"{title}: {entity_type}.")
        description = kg.get("description")
        if description:
            snippets.append(description)
        for attribute, value in kg.get("attributes", {}).items():
            snippets.append(f"{title} {attribute}: {value}.")

    for result in results[self.result_key_for_type[self.type]][: self.k]:
        if "snippet" in result:
            snippets.append(result["snippet"])
        for attribute, value in result.get("attributes", {}).items():
            snippets.append(f"{attribute}: {value}.")

    if len(snippets) == 0:
        return ["No good Google Search Result was found"]
    return snippets


def _parse_results(results: dict) -> str:
    return " ".join(_parse_snippets(results))


async def perform_web_search(query: str):
    """Search for a keyword using the Serper API"""
    current_date = datetime.now(timezone.utc)
    formatted_date = current_date.strftime("%B %d")
    formatted_year = current_date.strftime("%Y")
    updated_query = f"{query} (as of {formatted_date}, year {formatted_year})"

    response = search(search_keyword=updated_query)
    return _parse_results(results=response.json())
