import firebase_admin
from firebase_admin import firestore, credentials, auth
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1 import SERVER_TIMESTAMP
import requests
import re, asyncio
from typing import Optional, Any, Annotated
from config import (
    FIREBASE_PROJECT_ID,
    FIREBASE_PRIVATE_KEY,
    FIREBASE_CLIENT_EMAIL,
    FIREBASE_TOKEN_URI,
    FIREBASE_API_KEY,
)
from datetime import datetime, timedelta, time, timezone


cred = credentials.Certificate(
    {
        "type": "service_account",
        "project_id": FIREBASE_PROJECT_ID,
        "private_key": FIREBASE_PRIVATE_KEY,
        "client_email": FIREBASE_CLIENT_EMAIL,
        "token_uri": FIREBASE_TOKEN_URI,
    }
)

# List of Automated Chats ids:
AUTOMATED_CHATS = ["risky-chat", "conservative-chat", "degen-chat"]

if not firebase_admin.get_app():
    app = firebase_admin.initialize_app(cred)

db = firestore.client()

# scratchpad
local_collection = {}


def generate_firebase_id_token(user_id):
    # 1. Create a custom token
    custom_token = auth.create_custom_token(user_id)

    # 2. Exchange custom token for an ID token
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={FIREBASE_API_KEY}"

    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json={
            "token": custom_token.decode("utf-8"),  # Convert bytes to string
            "returnSecureToken": True,
        },
    )
    response.raise_for_status()  # Raise error for HTTP failures

    # Extract the ID token
    id_token = response.json()["idToken"]
    return id_token


# ==============================================================================
# ============================= Chat running utils =============================
# ==============================================================================


def clean_message(message: str) -> str:
    """
    Remove the 'using the ... agent' part from the message if it exists.
    """
    pattern = r"\susing the \S+ agent$"
    cleaned_message = re.sub(pattern, "", message)
    return cleaned_message


# ==============================================================================
# ========================  LP - Pools Registry ========================
# ==============================================================================
def db_save_pool_address_for_wallet(
    wallet_address: str, pool_address: str, protocol_name: str
):
    """
    Save the pool address for a wallet under a specific protocol.
    Params:
        wallet_address (str): wallet address that added liquidity to a pool.
        pool_address (str): pool address that the user added liquidity to.
        protocol_name (str): name of the protocol under which the pool is registered.
    """
    liquidity_pools_ref = db.collection("executor-model").document("liquidity-pools")
    wallet_pools_ref = (
        liquidity_pools_ref.collection("wallets")
        .document(wallet_address)
        .collection(protocol_name)
        .document("open_pools")
    )
    wallet_pools_ref.set({"pools": firestore.ArrayUnion([pool_address])}, merge=True)
    return True


def db_get_user_open_pools(wallet_address: str, protocol_name: str):
    liquidity_pools_ref = db.collection("executor-model").document("liquidity-pools")
    wallet_pools_ref = (
        liquidity_pools_ref.collection("wallets")
        .document(wallet_address)
        .collection(protocol_name)
        .document("open_pools")
    )
    doc = wallet_pools_ref.get()
    if not doc.exists:
        return []
    return doc.to_dict().get("pools", [])


def db_delete_pool_from_user_open_pools(
    wallet_address: str, pool_address: str, protocol_name: str
):
    liquidity_pools_ref = db.collection("executor-model").document("liquidity-pools")
    wallet_pools_ref = (
        liquidity_pools_ref.collection("wallets")
        .document(wallet_address)
        .collection(protocol_name)
        .document("open_pools")
    )
    wallet_pools_ref.set({"pools": firestore.ArrayRemove([pool_address])}, merge=True)
    return True


# ==============================================================================
# region New Functions to get Users, Wallets, and Chats for Re-Arch ============
# ==============================================================================
def get_user_wallets(user_id):
    try:
        wallets_collection_ref = db.collection("wallets")
        user_filter = FieldFilter("user_id", "==", user_id)
        query = wallets_collection_ref.where(filter=user_filter).get()

        if not query:
            return {}

        grouped_wallets = {
            "EVM": [],
            "SOLANA": [],
        }

        for doc in query:
            wallet_data = doc.to_dict()
            chain = wallet_data.get("chain")
            if chain in grouped_wallets and not grouped_wallets[chain]:
                grouped_wallets[chain].append(wallet_data)
            elif chain not in grouped_wallets:
                print(f"Unexpected chain value: {chain}")

        return {
            chain: wallets[0] for chain, wallets in grouped_wallets.items() if wallets
        }

    except Exception as e:
        print(f"An error occurred: {e}")
        return {}


def get_messages_by_chat(chat_id, collection_name="chats"):
    chat_ref = db.collection(collection_name).document(chat_id)
    if not chat_ref.get().exists:
        return None
    messages = (
        chat_ref.collection("messages")
        .order_by("createdAt", direction=firestore.Query.DESCENDING)
        .limit(6)
        .get()
    )

    # Transform each message to the desired format
    formatted_messages = [
        {
            "role": "user" if msg.to_dict().get("sender") == "user" else "assistant",
            "content": msg.to_dict().get("content_hidden", None)
            or msg.to_dict().get("content", ""),
        }
        for msg in messages
        if msg.to_dict().get("messageType")
        in ["text"]  # remove thoughts, transactions, or UI components
    ]
    return list(reversed(formatted_messages))


def db_save_chat(chat_id: str, user_id: str, collection_name="chats"):
    chat_doc_ref = db.collection(collection_name).document(chat_id)
    chat_doc_ref.set(
        {
            "userId": user_id,
            "createdAt": SERVER_TIMESTAMP,
            "updatedAt": SERVER_TIMESTAMP,
            "status": "pending",
            "deleted": False,
        }
    )


def db_save_message(
    chat_id: str,
    content: str,
    sender: str,
    message_type: str,
    user_id: str,
    metadata: dict = None,
    collection_name="chats",
):
    message_to_save = {
        "type": message_type,
        "content": content.replace(
            "TERMINATE", ""
        ),  # Trim 'TERMINATE' if not on the next run of the agent it's always ending up early
        "sender": sender,
        "userId": user_id,
        "messageType": message_type,
        "createdAt": SERVER_TIMESTAMP,
        "updatedAt": SERVER_TIMESTAMP,
        "status": "pending",
        "isRead": False,
    }
    if metadata is not None:
        message_to_save["metadata"] = metadata
    try:
        chat_ref = (
            db.collection(collection_name).document(chat_id).collection("messages")
        )
        chat_ref.add(message_to_save)
    except Exception as e:
        return e


def save_ui_message(
    chat_id: str,
    renderData: dict,
    component: str,
    metadata: dict = None,
    thought: str = None,
    isFinalThought: bool = False,
):
    try:
        user_id = get_request_ctx(parentKey=chat_id, key="user_id") or ""
        message_to_save = {
            "component": component,
            "sender": "ui",
            "userId": user_id,
            "renderData": renderData,
            "createdAt": SERVER_TIMESTAMP,
            "updatedAt": SERVER_TIMESTAMP,
        }
        if metadata is not None:
            message_to_save["metadata"] = metadata

        if thought:
            save_agent_thought(
                chat_id=chat_id,
                thought=thought,
                isFinalThought=isFinalThought,
            )

        chat_ref = db.collection("chats").document(chat_id)
        messages_ref = chat_ref.collection("messages")
        # If it's an automated chat, update the chat_ref updatedAt field (needed on main.py when user sending a message)
        if chat_id in AUTOMATED_CHATS:
            chat_ref.set({"updatedAt": SERVER_TIMESTAMP}, merge=True)

        messages_ref.add(message_to_save)
    except Exception as e:
        raise e


def db_get_chat_doc(chat_id: str):
    chat_doc = db.collection("chats").document(chat_id).get()
    if not chat_doc.exists:
        return None
    return chat_doc.to_dict()


def get_user_profile(user_id: str):
    user_ref = db.collection("users").document(user_id)

    user_snapshot = user_ref.get()

    if not user_snapshot.exists:
        return None

    user_data = user_snapshot.to_dict()
    return user_data


async def update_message(chat_id: str, user_id: str, message_id: str, data: dict):
    messages_ref = db.collection("chats").document(chat_id).collection("messages")
    message_doc_ref = messages_ref.document(message_id)
    doc = message_doc_ref.get()
    if doc.exists:
        doc_data = doc.to_dict()
        data["content"] = doc_data.get("content", "") + data.get("content", "")
        message_doc_ref.update({"updatedAt": SERVER_TIMESTAMP, **data})
    else:
        message_doc_ref.set(
            {
                "chatId": chat_id,
                "userId": user_id,
                "createdAt": SERVER_TIMESTAMP,
                "updatedAt": SERVER_TIMESTAMP,
                **data,
            }
        )


def create_message_doc_id(chat_id: str):
    messages_ref = db.collection("chats").document(chat_id).collection("messages")
    return messages_ref.document().id


# endregion


# ==============================================================================
# ========================== Get top traders wallets ===========================
# ==============================================================================


def get_top_traders_wallets():
    """
    Retrieve the list of top trader wallets from the Firestore database.

    Returns:
        list: A list of wallet addresses of the top traders.
    """
    try:
        top_traders_doc_ref = db.collection("top_traders_wallets").document("wallets")
        top_traders_doc = top_traders_doc_ref.get()

        if top_traders_doc.exists:
            addresses = top_traders_doc.to_dict().get("addresses", [])

            return addresses
        else:
            print("No top traders document found.")
            return []

    except Exception as e:
        print(f"Error retrieving top traders wallets: {e}")
        return []


def set_context_id(key: str):
    local_collection[key] = {"session_id": key}
    return key


def get_context_id(parentKey: str) -> Optional[str]:
    """Safely get the current context ID."""
    return local_collection.get(parentKey).get("session_id")


def send_message(
    chat_id: str, message_id: str, user_id: str, message: str, type: str = "ai"
) -> None:
    """Send a message to the client with type and optional parameters."""
    message_doc_ref = (
        db.collection("chats")
        .document(chat_id)
        .collection("messages")
        .document(message_id)
    )
    message_doc_ref.set(
        {
            "chatId": chat_id,
            "userId": user_id,
            "content": message.replace("TERMINATE", ""),
            "sender": "AI" if type == "ai" else "user",
            "messageType": "text",
            "status": "pending",
            "isRead": False,
            "createdAt": SERVER_TIMESTAMP,
            "updatedAt": SERVER_TIMESTAMP,
        }
    )


def set_request_ctx(parentKey: str, key: str, value: Any) -> Any:
    """Set a value in the request context."""
    local_collection[parentKey] = {**local_collection[parentKey], key: value}
    return value


def get_request_ctx(parentKey: str, key: str) -> Any:
    """Get a value from the request context."""
    return local_collection.get(parentKey, {}).get(key, None)


def remove_request_ctx(key: str) -> None:
    """Remove a value from the request context."""
    local_collection[key] = None


def get_wallet_to_store_in_analytics(chat_id: str):
    """Get the wallet address to use for analytics, prioritizing Solana wallet if connected."""
    evm_wallet_address = get_request_ctx(chat_id, "evm_wallet_address")
    solana_wallet_address = get_request_ctx(chat_id, "solana_wallet_address")

    # As we are launching meme token on SOL, prioritize solana wallet if connected
    return solana_wallet_address or evm_wallet_address


def verify_api_key(api_key: str) -> bool:
    """Verify if an API key exists in the database.
    Args:
        api_key (str): The API key to verify
    Returns:
        bool: True if API key exists in database, False otherwise
    """
    try:
        api_keys_ref = db.collection("api-keys")
        query = api_keys_ref.where(filter=FieldFilter("apiKey", "==", api_key))
        docs = query.get()
        return len(docs) > 0
    except Exception as e:
        return False


def save_agent_thought(chat_id: str, thought: str, isFinalThought: bool = False):
    """
    Saves a thought process to Firebase.

    Args:
        chat_id (str): The chat ID where the thought should be saved
        thought (str): The thought/thinking process to save
    """
    # If it's evaluation do not save thoughts
    is_evaluation = get_request_ctx(parentKey=chat_id, key="evaluation_mode") or False
    if is_evaluation:
        return

    user_id = get_request_ctx(parentKey=chat_id, key="user_id") or ""
    message_to_save = {
        "component": "agent_thought",
        "sender": "agent",
        "userId": user_id,
        "thought": thought,
        "createdAt": SERVER_TIMESTAMP,
        "updatedAt": SERVER_TIMESTAMP,
        "messageType": "agent_thought",
        "metadata": {"isFinalThought": isFinalThought},
    }

    chat_ref = db.collection("chats").document(chat_id).collection("messages")
    chat_ref.add(message_to_save)


def update_tx_status(transaction_id: str, status: str, signature: str):
    """Update transaction status and hash in Firestore with history tracking."""
    try:
        transaction_ref = db.collection("transactions").document(transaction_id)
        transaction_ref.set({"status": status, "tx_hash": signature}, merge=True)

        history_doc = transaction_ref.collection("history").document()
        history_doc.set(
            {
                "status": status,
                "message": "",
                "timestamp": SERVER_TIMESTAMP,
            }
        )
        return True
    except Exception as error:
        print(f"Error updating transaction status: {error}")
        return False


def update_unsigned_transactions(
    user_id: str, task_id: str, reset: bool = True
) -> bool:
    """Reset unsigned transactions to 0 when a user signs a scheduled tx"""
    try:
        task_ref = db.collection("scheduled_tasks").document(task_id)
        task_doc = task_ref.get()
        if not task_doc.exists:
            return False

        task_data = task_doc.to_dict()
        if task_data.get("userId") != user_id:
            raise Exception("Unauthorized: Task does not belong to the user")

        if reset:
            # reset unsigned_transactions to 0
            task_ref.update({"unsigned_transactions": 0})
        else:
            # increment it by 1, whatever its current value is
            task_ref.update({"unsigned_transactions": firestore.Increment(1)})
        return True
    except Exception as error:
        print(f"Error resetting unsigned transactions: {error}")
        raise error


def get_cached_tweets(usernames: list[str], limit: int = 5) -> list[dict]:
    """Get cached tweets from Firebase for the given usernames.

    Args:
        usernames (list[str]): List of Twitter usernames to get tweets for
        limit (int, optional): Maximum number of tweets per username. Defaults to 5.

    Returns:
        list[dict]: List of tweet objects
    """
    try:
        twitter_feeds_ref = db.collection("account_tweets_cache")
        tweets = []

        for username in usernames:
            query = (
                twitter_feeds_ref.where("username", "==", username)
                .order_by("lastUpdated", direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            docs = query.get()
            for doc in docs:
                data = doc.to_dict()["data"]
                tweets.append({**data, "username": username})

        return tweets
    except Exception as e:
        print(f"Error getting cached tweets: {e}")
        return []


# region Get Tweets for Market Context Agent


def _get_tweets_for_a_single_day_sync(day_date, limit):
    """Synchronous helper to fetch tweets for a single day using the existing db client."""
    twitter_feed_col_ref = db.collection("twitter-feeds")
    start_of_day = datetime.combine(day_date, time.min, tzinfo=timezone.utc)
    end_of_day = datetime.combine(day_date, time.max, tzinfo=timezone.utc)

    start_of_day_str = start_of_day.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_of_day_str = end_of_day.strftime("%Y-%m-%dT%H:%M:%S.999Z")

    top_tweets_snapshots = (
        twitter_feed_col_ref.where(
            filter=FieldFilter("createdAt", ">=", start_of_day_str)
        )
        .where(filter=FieldFilter("createdAt", "<=", end_of_day_str))
        .order_by("createdAt", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .get()
    )
    return [tweet.to_dict().get("text", "") for tweet in top_tweets_snapshots]


async def get_tweets_from_set_days(days: int, limit: int = 5):
    """
    Asynchronously retrieves top tweets from the current day to a specified number of days in the past
    by running synchronous queries in a thread pool.
    """
    today = datetime.now(timezone.utc).date()
    tasks = [
        asyncio.to_thread(
            _get_tweets_for_a_single_day_sync, today - timedelta(days=i), limit
        )
        for i in range(days)
    ]
    daily_tweets_lists = await asyncio.gather(*tasks)

    # Flatten the list of lists into a single list
    all_tweets = [tweet for sublist in daily_tweets_lists for tweet in sublist]
    return all_tweets


def save_market_context(dataToSave: dict):
    market_context_col_ref = db.collection("market-context")
    market_context_col_ref.add({**dataToSave, "createdAt": SERVER_TIMESTAMP})


# endregion


# region to get events based on tweets
def get_tweet_based_events_from_db():
    """
    Fetch all events from rumours_events collection where status is "pending" and tweetBased is true
    """
    try:
        # Query for events with status "pending" and tweetBased true
        events_ref = db.collection("rumours_events")
        query = (
            events_ref.where(filter=FieldFilter("tradeStatus", "==", "pending"))
            .where(filter=FieldFilter("tweetBased", "==", True))
            .where(filter=FieldFilter("executionTime", "==", None))
        )

        # Execute the query
        docs = query.stream()

        events = []
        for doc in docs:
            event_data = doc.to_dict()
            event_data["eventId"] = doc.id  # Add the document ID to the data
            events.append(event_data)

        return events

    except Exception as e:
        return []


# endregion


# region Polymarket Events
def check_event_exists_in_rumours(event_id: str):
    """
    Check if an event already exists in the rumours_events collection
    """
    try:
        rumours_ref = db.collection("rumours_events").document(event_id)
        doc = rumours_ref.get()
        return doc.exists
    except Exception as e:
        print(f"Error checking if event exists in rumours: {e}")
        return False


# Function to save the event to the database (rumours_events) after the agent has reviewed and validated the event
async def save_polymarket_event_to_rumours_collection(
    event_id: Annotated[str, "The id of the event to save."],
    new_title: Annotated[str, "The new title of the event."],
    new_description: Annotated[str, "The new description of the event."],
    is_tweet_based: Annotated[bool, "Whether the event is tweet based or not."],
):
    """
    Gets the event data from the polymarket_events collection with the event_id
    Copies and saves the event data to the rumours_events collection
    Uses embedding similarity to prevent duplicate events
    """
    try:
        from services.polymarket_similarity_service import (
            PolymarketSimilarityService,
        )

        # Initialize similarity service
        similarity_service = PolymarketSimilarityService()

        # Check if event already exists in rumours collection by ID
        if check_event_exists_in_rumours(event_id):
            return True

        # Check for similar events using embeddings
        similar_event = await similarity_service.check_similar_event_exists(
            title=new_title,
            similarity_threshold=0.35,  # Adjustable threshold for similarity detection
        )

        if similar_event:
            return True

        # Get original event data
        event_data = (
            db.collection("polymarket_events").document(event_id).get().to_dict()
        )

        # Update with agent-modified data
        event_data["title"] = new_title
        event_data["tweetBased"] = is_tweet_based
        event_data["description"] = new_description

        # if the event is tweet based, set the executionTime, eventTime, closingTime to None
        if is_tweet_based:
            event_data["executionTime"] = None
            event_data["eventTime"] = None
            event_data["closingTime"] = None

        # Save with embedding using the similarity service
        success = await similarity_service.save_event_with_embedding(
            event_id=event_id,
            event_data=event_data,
        )

        if success:
            return True
        else:
            return False

    except Exception as e:
        print(f"Error saving event to rumours collection: {e}")
        return False


# endregion


def get_enso_supported_chains_and_protocols():
    """
    Get the supported protocols for Enso from Firestore
    Returns: dict with chainId as key and dict with chain_name and protocols as value
    Example: {"8453": {"chain_name": "Base", "protocols": ["aave-v3", "morpho-blue-vaults"]}}
    """
    try:
        from services.chains import call_chains_service

        # Use the new structure: enso_supported_protocols collection
        enso_ref = db.collection("enso_supported_protocols")
        docs = enso_ref.stream()

        enhanced_data = {}

        for doc in docs:
            chain_id = doc.id  # Document ID is the chainId
            data = doc.to_dict()

            if data and "protocols" in data and isinstance(data["protocols"], list):
                try:
                    # Get chain name using call_chains_service
                    chain_name = call_chains_service(
                        method="getChainName", chainId=chain_id
                    )

                    enhanced_data[chain_id] = {
                        "chain_name": chain_name,
                        "protocols": data["protocols"],
                    }
                except Exception as chain_error:
                    print(f"Error getting chain name for {chain_id}: {chain_error}")
                    # Fallback: use chain_id as name if service fails
                    enhanced_data[chain_id] = {
                        "chain_name": chain_id,
                        "protocols": data["protocols"],
                    }

        return enhanced_data
    except Exception as e:
        print(f"Error getting Enso supported protocols: {e}")
        return {}


def get_enso_supported_tokens(
    chain_id: str = None, project: str = None, symbol: str = None
):
    """
    Get supported tokens from Enso Firestore database using optimized queries

    Args:
        chain_id (str, optional): Specific chain ID to query (e.g., "8453").
        project (str, optional): Filter by project name (e.g., "morpho").
        symbol (str, optional): Filter by token symbol (e.g., "USDC").

    Returns:
        list: List of token objects, filtered and sorted by APY (descending)
        Example: [{"apy": 12.35, "project": "morpho", "token": {...}, ...}, ...]
    """
    try:
        # Build query with filters
        tokens_ref = db.collection("enso_supported_tokens")
        query = tokens_ref

        # Apply filters
        if chain_id:
            query = query.where("chainId", "==", int(chain_id))
        if project:
            query = query.where("project", "==", project.lower())

        # Execute query
        docs = query.stream()
        all_tokens = []
        # Get supported protocols for chain names
        supported_protocols = get_enso_supported_chains_and_protocols()

        for doc in docs:
            token_data = doc.to_dict()

            # Apply symbol filter in Python (Firestore doesn't support case-insensitive queries)
            if symbol and symbol.lower() not in token_data.get("symbol", "").lower():
                continue

            # Transform to expected format
            chain_id_str = str(token_data.get("chainId"))
            chain_data = supported_protocols.get(chain_id_str, {})

            transformed_token = {
                "apy": token_data.get("apy", 0),
                "tvl": token_data.get("tvl", 0),
                "underlyingTokens": token_data.get("underlyingTokens", []),
                "project": token_data.get("project", ""),
                "token": {
                    "chainId": token_data.get("chainId"),
                    "chain": token_data.get("chain", ""),
                    "name": token_data.get("name", ""),
                    "symbol": token_data.get("symbol", ""),
                    "decimals": token_data.get("decimals", 18),
                    "address": token_data.get("address", ""),
                    "logo_uri": token_data.get("logoURI", ""),
                },
                "chain_id": chain_id_str,
                "chain_name": chain_data.get("chain_name", chain_id_str),
                "updated_at": token_data.get("updated_at"),
            }

            all_tokens.append(transformed_token)

        # Sort by APY (descending)
        all_tokens.sort(key=lambda x: x.get("apy", 0), reverse=True)

        return all_tokens
    except Exception as e:
        print(f"Error getting Enso supported tokens: {e}")
        return []
