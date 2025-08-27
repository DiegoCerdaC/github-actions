from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.tools import AgentTool
from services.llm import gpt_4o_client
from agents.researcher_agent.functions import get_comprehensive_market_data


def create_market_analysis_agent(chat_id: str, use_frontend_quoting: bool):
    """Performing extensive research and market analysis into current blockchain ecosystem.

    Args:
        chat_id (str): the current chat id
        use_frontend_quoting (bool): a boolean

    Returns:
        An Agent Tool: an executable agent tool that has capabilities to perform research and market analysis
        on current blockchain ecosystem.
    """
    market_analysis_agent = AssistantAgent(
        name="market_analysis_assistant",
        model_client=gpt_4o_client,
        system_message=(
            "You are a helpful assistant specializing in research and market analysis on current blockchain ecosystem.\n"
            "- Use get_comprehensive_market_data for market-related queries including:\n"
            "  * Current market status\n"
            "  * Market comparisons (24h, week, month)\n"
            "  * Market trends and changes\n"
            "  * Market performance analysis\n"
            "- ALWAYS use this function for ANY market-related query\n"
            "- Time comparison handling:\n"
            "  * For 24h comparisons: Use market_cap_change_24h and volume_change_24h\n"
            "  * For week comparisons: Use historical_comparison.week_ago data\n"
            "  * For month comparisons: Use historical_comparison.month_ago data\n"
            "- Set detailed_response=True for:\n"
            "  * Any comparison queries (vs yesterday, week ago, month ago)\n"
            "  * Detailed analysis requests\n"
            "  * Performance analysis over time\n"
            "- NEVER skip calling this function for market queries\n"
            "- NEVER return 'no access to real-time data' responses\n"
            "- ALWAYS use the data returned by this function\n"
            "Key Points:\n"
            f"- Current chat id is: {chat_id}. "
            f"- use_frontend_quoting is ALWAYS {use_frontend_quoting}."
        ),
        tools=[get_comprehensive_market_data],
        reflect_on_tool_use=True,
    )

    return AgentTool(agent=market_analysis_agent)