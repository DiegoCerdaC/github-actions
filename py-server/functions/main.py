import os
import dotenv

dotenv.load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

import firebase_admin
from firebase_admin import credentials
from firebase_functions.firestore_fn import (
    on_document_created,
    Event,
    DocumentSnapshot,
)
from firebase_functions.pubsub_fn import on_message_published, MessagePublishedData
from firebase_functions.options import MemoryOption
from firebase_functions.scheduler_fn import on_schedule
from firebase_functions.core import CloudEvent
from firebase_functions.https_fn import on_request, Request, Response
import asyncio

from config import (
    FIREBASE_PROJECT_ID,
    FIREBASE_PRIVATE_KEY,
    FIREBASE_CLIENT_EMAIL,
    FIREBASE_TOKEN_URI,
)

try:
    app = firebase_admin.get_app()
except ValueError:
    cred = credentials.Certificate(
        {
            "type": "service_account",
            "project_id": FIREBASE_PROJECT_ID,
            "private_key": FIREBASE_PRIVATE_KEY,
            "client_email": FIREBASE_CLIENT_EMAIL,
            "token_uri": FIREBASE_TOKEN_URI,
        }
    )
    app = firebase_admin.initialize_app(cred)


### Executor Agent Region
@on_document_created(
    document="chats/{chatId}/messages/{messageId}",
    memory=MemoryOption.MB_512,
    concurrency=10,
    min_instances=1,
    region="southamerica-east1",
)
def on_message_created(event: Event[DocumentSnapshot]) -> None:
    try:
        from executor import start_bot
        from services.voice import transcribe_audio
        from utils.firebase import update_message, db_save_message

        snapshot = event.data
        if not snapshot:
            return
        data = snapshot.to_dict()

        from utils.firebase import db_get_chat_doc, get_user_profile

        chat_id = event.params["chatId"]
        if data.get("sender") == "user" and data.get("messageType") == "text":
            chat_doc = db_get_chat_doc(chat_id=chat_id)
            if not chat_doc:
                return
            message_id = event.params["messageId"]
            user_id = chat_doc.get("userId", "") or data.get("userId", "")
            summary = chat_doc.get("summary", "")
            use_voice = data.get("useVoice", False)
            if use_voice and data.get("voiceContent") and not data.get("content"):
                content = transcribe_audio(data.get("voiceContent", ""))
                asyncio.run(
                    update_message(
                        chat_id=chat_id,
                        user_id=user_id,
                        message_id=message_id,
                        data={"content": content, "sender": "user"},
                    )
                )
            # get user profile & onboarding status
            user_profile = get_user_profile(user_id)
            onboarding_completed = user_profile.get(
                "onboarding_completed", "NOT_ONBOARDED"
            )

            if not onboarding_completed or onboarding_completed != "ONBOARDED":
                from agents.user_management.user_management_agent import (
                    call_user_management_agent,
                )

                asyncio.run(
                    call_user_management_agent(
                        task="onboarding",
                        user_id=user_id,
                        chat_id=chat_id,
                        use_voice=use_voice,
                    )
                )
                return
            else:
                asyncio.run(
                    start_bot(
                        user_id=user_id,
                        chat_id=chat_id,
                        integrator_id="sphereone",
                        summary=summary,
                        use_voice=use_voice,
                    )
                )
                return
        else:
            return
    except Exception as e:
        print("error: ", e)
        db_save_message(
            chat_id=chat_id,
            content=f"An error was encountered: {e}",
            sender="AI",
            message_type="text",
            user_id=user_id,
        )


### Summarizer Agent Region
@on_document_created(
    document="chats/{chatId}/messages/{messageId}",
    memory=MemoryOption.MB_512,
    region="southamerica-east1",
)
def on_message_created_summarize(event: Event[DocumentSnapshot]) -> None:
    try:
        from summarizer import summarize_chat

        snapshot = event.data
        if not snapshot:
            print("No data associated with the event")
            return

        chat_id = event.params["chatId"]

        # Run the summarizer in parallel to the executor

        # We don't want the summarizer to summarize the agent thought
        data = snapshot.to_dict()
        if data.get("component", "") == "agent_thought":
            return
        # We don't need to check for user/message type as we want to summarize all messages
        asyncio.run(summarize_chat(chat_id))
    except Exception as e:
        print("Error in summarizer: ", e)


# On Error Messages from Frontend
# Call ErrorAgent to handle it and reply back to the user on a "human way"
@on_document_created(
    document="error-messages/{chatId}/messages/{messageId}",
    memory=MemoryOption.MB_512,
    region="southamerica-east1",
)
def on_error_message_created(event: Event[DocumentSnapshot]) -> None:
    from error_agent import generate_error_message
    from utils.firebase import db_get_chat_doc

    try:
        snapshot = event.data
        data = snapshot.to_dict()
        if not snapshot:
            return

        chat_id = event.params["chatId"]
        chat_doc = db_get_chat_doc(chat_id=chat_id)

        if not chat_doc:
            return

        user_id = chat_doc.get("userId", "")
        chat_summary = chat_doc.get("summary", "")
        frontend_error = data.get("content", "")
        use_voice = data.get("useVoice", False)

        if not frontend_error:
            return
        asyncio.run(
            generate_error_message(
                chat_id, user_id, chat_summary, frontend_error, use_voice
            )
        )
    except Exception as e:
        print("Error in error agent: ", e)


### Automated Agents Chats Region
# Conservative Chat (Stake + Lulo) - run every 1 hour
@on_schedule(schedule="0 * * * *", memory=MemoryOption.MB_512, timeout_sec=540)
def on_conservative_agent_run(event: CloudEvent) -> None:
    try:
        from agents.conservative_agent.conservative_agent import call_conservative_agent

        chat_id = "conservative-chat"
        asyncio.run(call_conservative_agent(chat_id=chat_id))
    except Exception as e:
        print("Error running conservative agent: ", e)


# Degen Chat (Memecoin) - run every 15 minutes
@on_schedule(schedule="*/30 * * * *", memory=MemoryOption.MB_512, timeout_sec=540)
def on_degen_agent_run(event: CloudEvent) -> None:
    try:
        from agents.automated_memecoin_trader.memecoin_agent import (
            call_automated_memecoin_trader_agent,
        )

        chat_id = "degen-chat"
        asyncio.run(call_automated_memecoin_trader_agent(chat_id=chat_id))
    except Exception as e:
        print("Error running memecoin trader agent: ", e)


# Risky-chat (Drift) - run every 1 hours
@on_schedule(schedule="0 * * * *", memory=MemoryOption.MB_512, timeout_sec=540)
def on_autonomous_lulo_drift_agent_run(event: CloudEvent) -> None:
    from agents.autonomous_drift_agent.autonomous_drift_agent import (
        call_autonomous_drift_agent,
    )

    try:
        chat_id = "risky-chat"
        asyncio.run(call_autonomous_drift_agent(chat_id=chat_id))
    except Exception as e:
        print("Error running autonomous drift agent: ", e)


### Orbit Chat for MCP Region
@on_request(
    memory=MemoryOption.MB_512,
    region="southamerica-east1",
)
def call_orbit(request: Request) -> Response:
    from executor_mcp import start_chat
    from utils.firebase import verify_api_key
    from flask import jsonify

    try:
        if request.method != "POST":
            return jsonify({"error": "Method Not Allowed"}), 405

        api_key = request.headers.get("api-key")
        if not api_key:
            return jsonify({"error": "API key is required"}), 401

        if not verify_api_key(api_key):
            return jsonify({"error": "Invalid API key"}), 401

        data = request.get_json()
        user_id = data.get("userId")
        chat_id = data.get("chatId")
        prompt = data.get("prompt")
        sol_wallet_address = data.get("solWalletAddress")
        evm_wallet_address = data.get("evmWalletAddress")

        result = asyncio.run(
            start_chat(
                user_id=user_id,
                chat_id=chat_id,
                prompt=prompt,
                sol_wallet_address=sol_wallet_address,
                evm_wallet_address=evm_wallet_address,
            )
        )
        return jsonify({"result": result})

    except Exception as e:
        print("Error in request handler: ", e)
        return jsonify({"error": str(e)}), 500


# ### Event Trigger Agent Evaluation Endpoint
# @on_request(
#     memory=MemoryOption.MB_512,
#     region="southamerica-east1",
#     timeout_sec=540,
# )
# def test_event_trigger_agent(request: Request) -> Response:
#     from flask import jsonify

#     try:
#         if request.method != "GET":
#             return jsonify({"error": "Method Not Allowed. Use GET."}), 405

#         from eval.event_trigger_agent.event_trigger_agent_eval import (
#             run_eval_for_event_trigger_agent,
#         )

#         result = asyncio.run(run_eval_for_event_trigger_agent())

#         # Create response
#         response_data = {"success": True, "message": result}

#         # Return response immediately
#         return jsonify(response_data), 200

#     except asyncio.TimeoutError as e:
#         print(f"[ERROR] Timeout error in evaluation endpoint: {e}")
#         return jsonify({"success": False, "error": "Request timed out"}), 408
#     except Exception as e:
#         print(f"[ERROR] Error in evaluation endpoint: {e}")
#         return jsonify({"success": False, "error": str(e)}), 500


@on_message_published(
    topic="on-automated-transaction",
    memory=MemoryOption.MB_512,
    region="southamerica-east1",
)
def call_automated_orbit(event: CloudEvent[MessagePublishedData]) -> None:
    from automated_executor import start_automated_executor

    try:
        data = event.data.message.json
    except Exception as e:
        print(f"Error parsing message data: {e}")
        return

    if data is None:
        return

    try:
        user_id = data.get("userId", "")
        chat_id = data.get("chatId", "")
        prompt = data.get("prompt", "")
        sol_wallet_address = data.get("solWalletAddress", "")
        evm_wallet_address = data.get("evmWalletAddress", "")

        asyncio.run(
            start_automated_executor(
                user_id=user_id,
                chat_id=chat_id,
                prompt=prompt,
                sol_wallet_address=sol_wallet_address,
                evm_wallet_address=evm_wallet_address,
            )
        )
        return

    except Exception as e:
        print("Error in request handler: ", e)
        return


### For Orbit Terminal Market Context
@on_schedule(
    schedule="0 */2 * * *",  # every 2 hours
    memory=MemoryOption.MB_512,
    region="southamerica-east1",
    timeout_sec=540,
)
def on_market_analysis_run(event: CloudEvent) -> None:
    from agents.researcher_agent.market_context_agent import call_market_context_agent

    try:
        task = "current market trends and their impacts on BTC, SOL, ETH"
        asyncio.run(
            call_market_context_agent(
                task=task,
                chat_id="0",
                use_frontend_quoting=False,
            )
        )
    except Exception as e:
        print("Error running market context agent: ", e)


### Tweet Cache Listener Region
@on_document_created(
    document="twitter-feeds/{tweetId}",
    memory=MemoryOption.MB_512,
    region="southamerica-east1",
    timeout_sec=540,
)
def on_tweet_added(event: Event[DocumentSnapshot]) -> None:
    from utils.firebase import get_tweet_based_events_from_db
    from agents.event_trigger_agent.event_trigger_agent import call_event_trigger_agent

    try:
        snapshot = event.data
        if not snapshot:
            return

        tweet_data = snapshot.to_dict()

        if tweet_data:
            tweet_content = tweet_data.get("text", None)
            pending_events = get_tweet_based_events_from_db()
            if len(pending_events) > 0 and tweet_content:
                chat_result = asyncio.run(
                    call_event_trigger_agent(tweet=tweet_data, events=pending_events)
                )
                return chat_result
        return "No events to trigger"

    except Exception as e:
        print(f"Error processing tweet: {e}")


### Polymarket Events Listener Region
@on_document_created(
    document="polymarket_events/{eventId}",
    memory=MemoryOption.MB_512,
    region="southamerica-east1",
    timeout_sec=540,
)
def on_polymarket_event_added(event: Event[DocumentSnapshot]) -> None:
    from agents.polymarket_analysis_agent.polymarket_analysis_agent import (
        call_polymarket_analysis_agent,
    )

    def remove_non_ascii(text: str) -> str:
        """Remove all non-ASCII characters from the input string."""
        return "".join(char for char in text if ord(char) < 128)

    try:
        snapshot = event.data
        if not snapshot:
            return

        snapshot_data = snapshot.to_dict()

        event_data = {
            "id": snapshot_data["id"],
            "title": remove_non_ascii(snapshot_data["title"]),
            "description": remove_non_ascii(snapshot_data["description"]),
        }

        if event_data:
            result = asyncio.run(
                call_polymarket_analysis_agent(
                    event_data=event_data,
                )
            )
            # Ensure the result is properly encoded for printing
            try:
                print(f"Polymarket event analysis completed: {result}")
            except UnicodeEncodeError:
                # If there are encoding issues, print a sanitized version
                sanitized_result = result.encode("ascii", "ignore").decode("ascii")
                print(f"Polymarket event analysis completed: {sanitized_result}")
            return result

    except Exception as e:
        print(f"Error processing polymarket event: {e}. Event ID: {snapshot.id}")
