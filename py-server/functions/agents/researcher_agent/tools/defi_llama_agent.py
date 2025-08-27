from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.tools import AgentTool
from services.llm import gpt_4o_mini_client
from agents.researcher_agent.functions import (
    get_top_protocols_by_chain_on_defi_llama,
    get_top_chains_by_tvl_on_defi_llama,
    get_top_dexs_by_chain_on_defi_llama,
    get_top_yields_pools_by_chain_on_defi_llama,
)


def create_defi_llama_agent(chat_id: str, use_frontend_quoting: bool):
    """Retrieving information on Protocols, Chains, DEXs and Yields Pools through DeFi Llama.

    Args:
        chat_id (str): the current chat id
        use_frontend_quoting (bool): a boolean

    Returns:
        An Agent Tool: an executable agent tool that has capabilities to information from DeFi Llama
        about protocols, chains dexes, and yield pools.
    """
    defi_llama_agent = AssistantAgent(
        name="defi_llama_assistant",
        model_client=gpt_4o_mini_client,
        system_message=(
            "You are a helpful assistant specializing in retrieving information on Protocols, Chains, DEXs and Yields Pools on DeFi Llama:\n"
            "- Use get_top_protocols_by_chain_on_defi_llama for top protocols by chain\n"
            "- Use get_top_chains_by_tvl_on_defi_llama for top chains by TVL\n"
            "- Use get_top_dexs_by_chain_on_defi_llama for top DEXs by chain\n"
            "- Use get_top_yields_pools_by_chain_on_defi_llama for top yields pools by chain\n"
            "Key Points:\n"
            f"- Current chat id is: {chat_id}. "
            f"- use_frontend_quoting is ALWAYS {use_frontend_quoting}."
        ),
        tools=[
            get_top_protocols_by_chain_on_defi_llama,
            get_top_chains_by_tvl_on_defi_llama,
            get_top_dexs_by_chain_on_defi_llama,
            get_top_yields_pools_by_chain_on_defi_llama
        ],
        reflect_on_tool_use=True,
    )

    return AgentTool(agent=defi_llama_agent)