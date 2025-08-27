from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.tools import AgentTool
from services.llm import gpt_4o_mini_client
from agents.researcher_agent.functions import (
    analyze_portfolio_history,
)


def create_portfolio_agent(chat_id: str, use_frontend_quoting: bool):
    """Retrieve user wallet and portfolio information.

    Args:
        chat_id (str): the current chat id
        use_frontend_quoting (bool): a boolean

    Returns:
        An Agent Tool: an executable agent tool that has capabilities to retrieve user portfolio and wallet information.
    """
    portfolio_agent = AssistantAgent(
        name="portfolio_assistant",
        model_client=gpt_4o_mini_client,
        system_message=(
            "You are a helpful assistant specializing in retrieving a user's wallet and portfolio and providing deep analysis."
            "- Use analyze_portfolio_history to get performance metrics\n"
            "- By default, provide a concise response (5-7 lines) with:\n"
            "  - Current total value\n"
            "  - Change from yesterday (if available)\n"
            "  - Longest available period change (e.g., 7, 15, or 30 days)\n"
            "  - All-time change (if data exists)\n"
            "- Format example:\n"
            "  'Your portfolio is worth $X.\n"
            "   Yesterday to today: +$Y (Z%) [or 'No data from yesterday']\n"
            "   In N days: +$Y (Z%) [approximated if not exact]\n"
            "   Total: +$Y (Z%)'\n"
            "- Use '+' for gains, '-' for losses, and round to 2 decimals\n"
            "- If no exact data for a period, mark it as 'approximated' or skip it\n"
            "- For detailed requests (e.g., 'detailed analysis'), show all available periods\n"
            "Key Points:\n"
            f"- Current chat id is: {chat_id}. "
            f"- use_frontend_quoting is ALWAYS {use_frontend_quoting}."
        ),
        tools=[analyze_portfolio_history],
        reflect_on_tool_use=True,
    )

    return AgentTool(agent=portfolio_agent)