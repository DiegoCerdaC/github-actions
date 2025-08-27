from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.tools import AgentTool
from services.llm import gpt_4o_mini_client
from agents.researcher_agent.functions import (
    get_dexscreener_latest_boosted_tokens,
    get_dexscreener_most_boosted_tokens,
    get_dexscreener_latest_tokens,
    get_dexscreener_token_pair_info,
)


def create_dexscreener_agent(chat_id: str, use_frontend_quoting: bool):
    """Retrieving information on token information from Dexscreener such as boosted tokens, new/latest tokens, and token pair lookups.

    Args:
        chat_id (str): the current chat id
        use_frontend_quoting (bool): a boolean

    Returns:
        An Agent Tool: an executable agent tool that has capabilities to information from Dexscreener
        about boosted tokens, new/latest tokens, and token pair lookups.
    """
    dexscreener_agent = AssistantAgent(
        name="dexscreener_assistant",
        model_client=gpt_4o_mini_client,
        system_message=(
            "You are a helpful assistant specializing in retrieving information on boosted tokens, new/latest tokens, and token pair lookups.\n"
            "- Top 10 boosted tokens: use get_dexscreener_most_boosted_tokens\n"
            "- Latest boosted tokens: use get_dexscreener_latest_boosted_tokens\n"
            "- New tokens: use get_dexscreener_latest_tokens\n"
            "- Token pair lookup: get_dexscreener_token_pair_info (needs both token symbols)\n"
            "Key Points:\n"
            f"- Current chat id is: {chat_id}. "
            f"- use_frontend_quoting is ALWAYS {use_frontend_quoting}."
        ),
        tools=[
            get_dexscreener_latest_boosted_tokens,
            get_dexscreener_most_boosted_tokens,
            get_dexscreener_latest_tokens,
            get_dexscreener_token_pair_info
        ],
        reflect_on_tool_use=True,
    )

    return AgentTool(agent=dexscreener_agent)