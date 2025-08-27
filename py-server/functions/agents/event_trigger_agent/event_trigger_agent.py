from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from typing import Annotated, TypedDict, Optional
from services.llm import gpt_4o_client
import services.analytics as analytics
from utils.firebase import db
from datetime import datetime, timedelta
from firebase_admin import firestore
from utils.firebase import get_request_ctx, set_request_ctx

from services.tracing import (
    set_status_ok,
    set_status_error,
    tracer,
    set_attributes,
)


class TweetData(TypedDict):
    author: dict  # Contains username, name, authorId, profileUrl
    text: str
    createdAt: str
    id: str


class EventData(TypedDict):
    longTrades: list
    eventTime: Optional[any]
    shortTrades: list
    closingTime: Optional[any]
    title: str
    createdAt: any
    executionTime: Optional[any]
    executed: bool
    tradeStatus: str
    tweetBased: bool
    eventId: str


def updateExecutionTimeForEvent(
    eventId: Annotated[str, "The ID of the event to update"],
    tweetContent: Annotated[str, "The content of the tweet that triggered the event"],
    username: Annotated[str, "The username of the user who tweeted"],
    tweetId: Annotated[str, "The ID of the tweet that triggered the event"],
    is_evaluation: Annotated[bool, "Whether it's an Eval of the agent or a real run"],
    chat_id: Annotated[str, "The chat id"],
):
    """
    Updates the execution time for an event in the database.
    Only one event id per function call is allowed.
    Setting timestamp as current date

    Args:
        eventId (str): The ID of the event to update
        tweetContent (str): The content of the tweet that triggered the event
        username (str): The username of the user who tweeted
        tweetId (str): The ID of the tweet that triggered the event

    Returns:
        str: Response from the agent indicating the success or failure of processing
    """
    try:
        if is_evaluation:
            # Add event information to the context array for evaluation tracking
            current_events = get_request_ctx(chat_id, "triggered_events") or []
            event_info = {
                "eventId": eventId,
                "tweetContent": tweetContent,
                "username": username,
                "tweetId": tweetId,
            }
            current_events.append(event_info)
            set_request_ctx(chat_id, "triggered_events", current_events)
            return
        else:
            event_ref = db.collection("rumours_events").document(eventId)

            if event_ref.get().exists:
                # Use current time as base
                current_time = datetime.now()
                current_time = current_time.replace(
                    second=0, microsecond=0
                )  # Round to minute

                execution_time = firestore.SERVER_TIMESTAMP

                # Calculate eventTime (10 minutes after current time)
                event_time = current_time + timedelta(minutes=10)

                # Calculate closingTime (40 minutes after current time)
                closing_time = current_time + timedelta(minutes=40)

                event_ref.update(
                    {
                        "executionTime": execution_time,
                        "eventTime": event_time,
                        "closingTime": closing_time,
                        "triggeredBy": {
                            "tweetId": tweetId,
                            "tweetContent": tweetContent,
                            "username": username,
                        },
                    }
                )
                return (
                    "Execution time, event time, and closing time updated successfully"
                )
            else:
                return "Event not found"
    except Exception as e:
        return f"An error occurred: {str(e)}"


@tracer.start_as_current_span("event_trigger_agent")
async def call_event_trigger_agent(
    tweet: TweetData,
    events: list[EventData],
    chat_id: str = "automated-event-trigger-agent-chat",
    use_frontend_quoting: bool = False,
    is_evaluation: bool = False,
) -> Annotated[str, "The result of processing the tweet and events."]:
    """
    Compares tweet content with a list of events and updates execution times for matching events.

    This agent analyzes the content of a tweet and compares it against a list of events.
    If an event is related to the tweet content, it updates the event's execution time
    and closing time to trigger the event based on the tweet.

    Args:
        tweet (TweetData): The tweet data containing username, content, and date
        events (list[EventData]): List of events to compare against the tweet
        chat_id (str): The current chat id for tracking
        use_frontend_quoting (bool): Whether to use frontend quoting functionality

    Returns:
        str: Response from the agent indicating the success or failure of processing
    """

    if not is_evaluation:
        analytics.increment_agent_used("event_trigger_agent", chat_id)
    set_attributes(
        {
            "chat_id": chat_id,
            "task": "compare events with tweet",
            "use_frontend_quoting": use_frontend_quoting,
        }
    )

    tweet_content = tweet.get("text", None)
    username = tweet.get("author", {}).get("username", None)
    tweet_id = tweet.get("id", None)

    event_trigger_agent = AssistantAgent(
        name="event_trigger_agent",
        system_message=(
            "You are an expert AI agent specialized in analyzing tweets and determining if they are related to specific events. "
            "Your primary function is to compare tweet content with event titles and descriptions to identify when events have occurred."
            "\n\n"
            "CRITICAL RESPONSIBILITY: "
            "When you detect that a tweet's content indicates an event has happened, you MUST call the 'updateExecutionTimeForEvent' function "
            "with the corresponding eventID to update the execution time, username, and tweetContent."
            "ALWAYS call the function 'updateExecutionTimeForEvent when you find a match. Do NEVER skip this step because it's your main responsability."
            "\n\n"
            "ANALYSIS PROCESS: "
            "1. Carefully read the tweet content and analyze its meaning "
            "2. Compare it against each event's title and description "
            "3. Look for semantic relationships, not just exact word matches "
            "4. Consider synonyms, related concepts, and contextual relevance "
            "\n\n"
            "EXAMPLE SCENARIOS: "
            "- Event: 'BTC Creator is discovered' + Tweet: 'Satoshi Nakamoto was found. He is John Peter Doe.' → MATCH (call updateExecutionTimeForEvent) "
            "- Event: 'Ethereum Foundation disappear' + Tweet: 'Vitalik Buterin announces EF shutdown' → MATCH (call updateExecutionTimeForEvent) "
            "- Event: 'Major crypto exchange hack' + Tweet: 'Binance reports security breach' → MATCH (call updateExecutionTimeForEvent) "
            "\n\n"
            "DECISION CRITERIA: "
            "- Be conservative but thorough in your analysis "
            "- When in doubt about relevance, err on the side of caution and call the function "
            "- Consider both direct mentions and implied relationships "
            "- Look for news, announcements, discoveries, or revelations that match event themes "
            "\n\n"
            "ECONOMIC DATA RULE: "
            "Economic events without country specification (inflation, CPI, unemployment, rates, GDP, trade data, etc.) default to USA. "
            "Only match tweets that explicitly mention US/American economic data or USA specifically. "
            "Reject tweets about other countries' economic data unless the event explicitly mentions that country. "
            "Example if the tweet is about Jamaica indicators, and the event is related to Argentina indicators, it should NOT trigger the event. "
            "Geographic matching is required - both event and tweet must reference the same country for non-US economic data. "
            "\n\n"
            "POTENTIALITY RULE: "
            "DO NOT CALL updateExecutionTimeForEvent if the tweet describes potential events, future possibilities, or things that might happen. "
            "Only call the function when the tweet clearly states that the event HAS ALREADY HAPPENED. "
            "The tweet must confirm the event occurred, not that it's being considered or planned. "
            "\n\n"
            "FUNCTION CALL: "
            "When you identify a match, immediately call 'updateExecutionTimeForEvent' with the eventID (not the title, the eventId)"
            f"The parameter 'is_evaluation' should always be {is_evaluation}"
            f"The tweet id is: {tweet_id}"
            f"The chat id is: {chat_id}"
            f"The tweet content is: {tweet_content} and the username is: {username}"
            "Only one eventId per function call is allowed. Call the function one time for every matching event using its eventId."
            "\n\n"
            "IMPORTANT: Your decisions directly affect automated trading and wallet operations. "
            "Be precise, thorough, and always err on the side of triggering events when there's reasonable doubt. "
            "Missing a relevant tweet could mean missing critical trading opportunities. "
        ),
        model_client=gpt_4o_client,
        reflect_on_tool_use=False,
        tools=[updateExecutionTimeForEvent],
    )

    try:
        # We'll process the events in batches of 5, running the analysis for each batch.
        batch_size = 5
        for i in range(0, len(events), batch_size):
            try:
                events_batch = events[i : i + batch_size]
                updated_task = f"Analyze the following tweet: {tweet} and compare it against the following events: {events_batch}"

                await event_trigger_agent.on_messages(
                    messages=[TextMessage(content=updated_task, source="user")],
                    cancellation_token=CancellationToken(),
                )
            except Exception as e:
                print(
                    f"An error occurred processing task:{updated_task} \n Error:{str(e)}"
                )
    except Exception as e:
        set_status_error(e)
        return f"An error occurred: {str(e)}"

    set_status_ok()
    return f"I've completed the task. All the events were checked"
