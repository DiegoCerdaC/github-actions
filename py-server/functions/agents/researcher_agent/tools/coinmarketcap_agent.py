from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.tools import AgentTool
from services.llm import gpt_4o_mini_client
from agents.researcher_agent.functions import (
    get_highest_cryptocurrencies_gainers,
    get_cryptocurrencies_by_tags,
    get_cryptocurrency_by_symbol,
)


def create_coinmarketcap_agent(chat_id: str, use_frontend_quoting: bool):
    """Retrieving information on trending tokens and price information from Coinmarketcap.

    Args:
        chat_id (str): the current chat id
        use_frontend_quoting (bool): a boolean

    Returns:
        An Agent Tool: an executable agent tool that has capabilities to information from Coinmarketcap
        about trending tokens and prices.
    """
    coinmarketcap_agent = AssistantAgent(
        name="coinmarketcap_assistant",
        model_client=gpt_4o_mini_client,
        system_message=(
            "You are a helpful assistant specializing in retrieving information on trending tokens, and prices.\n"
            f"Current chat id is: {chat_id}. "
            f"And use_frontend_quoting is ALWAYS {use_frontend_quoting}.\n"
            "Trending & Hot Tokens:\n"
            "- Use get_highest_cryptocurrencies_gainers for overall trends\n"
            "- For specific tokens: get_cryptocurrency_by_symbol\n"
            "- Get coins by category using get_cryptocurrencies_by_tags\n"
            "- Never show internal IDs to users\n"
        ),
        tools=[
            get_highest_cryptocurrencies_gainers,
            get_cryptocurrencies_by_tags,
            get_cryptocurrency_by_symbol,
        ],
        reflect_on_tool_use=True,
    )

    return AgentTool(agent=coinmarketcap_agent)