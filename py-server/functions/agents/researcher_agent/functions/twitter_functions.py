import requests
import os
import json
from config import TWITTER_BEARER_TOKEN
from utils.firebase import save_ui_message, get_cached_tweets

BASE_URL = "https://api.x.com/2"


def search_user_by_usernames(usernames: list[str]):
    """Search Twitter/X users by usernames.
    This can search a single user or multiple users.

    # Parameters:
        usernames (list[str]): A list of usernames to search. Can be a list of one username or a list of many usernames.

    Raises:
        Exception: If 429, Twitter/X API Rate limit is reached.
        Exception: Other than 200 or 429 for internal server errors.

    # Returns:
        list[dict]: A list of twitter user objects that best match the usernames.
    """
    # check if it has values
    if not usernames:
        return "Please provide valid usernames to search."
    # clean out any twitter names like @orbitcryptoai and pass in orbitcryptoai as valid
    cleaned_usernames = [
        username[1:] if username.startswith("@") else username for username in usernames
    ]

    usernameParams = (
        ",".join(cleaned_usernames)
        if len(cleaned_usernames) > 1
        else cleaned_usernames[0]
    )
    response = requests.get(
        f"{BASE_URL}/users/by?usernames={usernameParams}&user.fields=description,profile_image_url",
        headers={"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"},
    )
    if response.status_code == 429:
        raise Exception("X API rate limit exceeded.")
    elif response.status_code != 200:
        raise Exception(f"X API error: {response.text}")
    else:
        users = response.json().get("data", [])
        return users


def save_tweets_to_render(
    chat_id, tweets, agent="researcher_agent", component="twitter_posts"
):
    """Save tweets to the database as a transaction.

    # Parameters:
        tweets (list[dict]): List of tweets to save to the database.
        agent (str): The agent name associated with this transaction.
        component (str): The UI component to render the tweets in.

    # Returns:
        dict: The saved transaction data or None if no chat_id is available.
    """

    return save_ui_message(
        chat_id=chat_id,
        renderData={"tweets": tweets},
        component=component,
        metadata={"agent": agent},
    )


def get_recent_twitter_posts(chat_id: str, username: str, amount: int = 10):
    """Get the 10 most recent tweets by specified user.

    # Parameters:
        chat_id (str): The current chat id
        username (str): Username of the user to search for their most recent tweets.
        amount (int): Number of tweets to return. Defaults to 10 if not specified.

    Raises:
        Exception: If 429, Twitter/X API Rate limit is reached.
        Exception: Other than 200 or 429 for internal server errors.

    # Returns:
        Union[str, list[dict]]: "Successful" if direct_render=True, otherwise list of tweets.
    """
    if not username:
        return "Please provide a valid username."

    cleaned_username = username.lstrip("@")

    query_params = f"query=from:{cleaned_username}&tweet.fields=created_at&expansions=author_id&user.fields=created_at"
    if amount > 10 and amount <= 20:
        query_params += f"&max_results={amount}"

    response = requests.get(
        f"{BASE_URL}/tweets/search/recent?{query_params}",
        headers={"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"},
    )

    if response.status_code == 429:
        raise Exception("X API rate limit exceeded.")
    elif response.status_code != 200:
        raise Exception(f"X API error: {response.text}")

    tweets = response.json().get("data", [])
    for tweet in tweets:
        tweet["username"] = cleaned_username

    if amount < 10:
        tweets = tweets[:amount]

    if chat_id:
        save_tweets_to_render(chat_id=chat_id, tweets=tweets)

    return tweets


def load_twitter_accounts():
    """Load Twitter accounts from the config file.

    # Parameters:
    - None

    # Returns:
    - List[str]: A list of Twitter accounts.
    """
    config_path = os.path.join(os.path.dirname(__file__), "twitter_accounts.json")
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading Twitter accounts: {e}")
        return {"accounts": []}


def get_tweets_from_key_accounts(chat_id: str | None = None):
    """Get the tweets from the key accounts using cached tweets from Firebase."""
    accounts = load_twitter_accounts()
    usernames = [account["twitter_handle"].lstrip("@") for account in accounts.get("accounts", [])]
    
    # Call the Firebase function to get cached tweets
    tweets = get_cached_tweets(usernames)
    
    if chat_id:
        save_tweets_to_render(chat_id=chat_id, tweets=tweets)
    
    return tweets
