from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from agents.researcher_agent.functions.common_functions import search_on_google, Timeframe
from services.llm import gpt_4o_client
from utils.firebase import get_tweets_from_set_days, save_market_context
import services.analytics as analytics
from services.tracing import set_status_ok, set_status_error, tracer, set_attributes


@tracer.start_as_current_span("market_context_agent")
async def call_market_context_agent(task: str, chat_id: str, use_frontend_quoting: bool = True):
    try:
        analytics.increment_agent_used("market_context_agent", chat_id)
        set_attributes(
            {"chat_id": chat_id, "task": task, "use_frontend_quoting": use_frontend_quoting}
        )
        # get top recent 20 tweets from current day to past 3 days
        top_tweets = await get_tweets_from_set_days(days=4, limit=20)

        # get web searches
        searches = await search_on_google(search_keywords_list=[task], timeframe=Timeframe.WEEK.value)

        market_context_agent = AssistantAgent(
            name="market_context_assistant",
            model_client=gpt_4o_client,
            system_message=(
                "You are a helpful assistant that can provide extensive insight into current market trends for a particular token(s).\n"
                "Analyze the provided tweets and identify any current major events or trends. "
                "Then, determine how they impacted the given task, whether to cause price to go up/down, bullish, positive/negative trend, etc.\n"
                "When analyzing tweets, do ignore tweets like 'The price of XXX is now $100,0000' or 'this is fire!'. And make no mentions of 'tweets'.\n"
                "Provide an extensive summary of the current events and how it impacted the given: {task}."
            ),
            reflect_on_tool_use=True,
        )

        updated_task = (
            f"Here is the current task: {task}\n"
            f"Here are the current tweets: {top_tweets}.\n"
        )

        chat_result = await market_context_agent.on_messages(
            messages=[TextMessage(content=updated_task, source="user")],
            cancellation_token=CancellationToken(),
        )
        content = chat_result.chat_message.content
        save_market_context({ "result": content, "recent_searches": searches })
        set_status_ok()
        return "Completed successfully"
    except Exception as e:
        set_status_error(e)
        return f"An error occurred in the call_market_context_agent: {str(e)}"

