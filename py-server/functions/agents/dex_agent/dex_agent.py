from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from typing import Annotated

from services.llm import gpt_4o_client
from agents.dex_agent.jupiter_functions import jupiter_get_quotes
from agents.dex_agent.lifi_functions import lifi_get_quote
from utils.firebase import get_request_ctx
import services.analytics as analytics
from services.tracing import set_status_ok, set_status_error, tracer, set_attributes
from agents.dex_agent.stake_functions import (
    get_user_staked_balances,
    supported_pools_and_tickers,
)


@tracer.start_as_current_span("dex_agent")
async def call_dex_agent(
    task: str, chat_id: str, use_frontend_quoting: bool = True
) -> Annotated[str, "The result of creating the swap or bridge transaction."]:
    """
    DEX agent for swaps and bridges on SOLANA and EVM Chains
    Uses Jupiter or LIFI to get the best quote for the transaction based on the chains involved.
    Args:
        task (str): Transaction description with chains, tokens, and amount
        chat_id (str): The current chat id
        use_frontend_quoting (bool): Whether to use frontend quoting or not
    Returns:
        str: Result or error description
    """
    try:
        analytics.increment_agent_used("dex", chat_id)
        set_attributes(
            {
                "chat_id": chat_id,
                "task": task,
                "use_frontend_quoting": use_frontend_quoting,
            }
        )

        wallet_address = get_request_ctx(chat_id, "solana_wallet_address")

        dex_agent = AssistantAgent(
            name="dex_agent",
            system_message=(
                "You are a blockchain assistant that helps users with swaps, bridges, and staking on SOLANA and EVM chains.\n"
                "For swaps/bridges: Use 'jupiter_get_quotes' if both chains are Solana, or 'lifi_get_quote' for EVM↔EVM, Solana↔EVM, or EVM↔Solana.\n"
                f"For staking/unstaking, supported Pools and tickers are: {supported_pools_and_tickers}\n"
                "For stake/unstake transactions:\n"
                "1. If the user specifies the ticker to stake into, use 'jupiter_get_quotes' and set transaction_type to stake/unstake.\n"
                "Use 'get_user_staked_balances' to show user's staked balances\n"
                "Always ensure all required information is provided and reply with clear results.\n"
                f"And use_frontend_quoting is ALWAYS {use_frontend_quoting}. "
            ),
            model_client=gpt_4o_client,
            reflect_on_tool_use=False,
            tools=[
                jupiter_get_quotes,
                lifi_get_quote,
                get_user_staked_balances,
            ],
        )

        updated_task = (
            f"Task: '{task}'\nWallet address: {wallet_address}.\nChatId is {chat_id}"
        )

        chat_result = await dex_agent.on_messages(
            messages=[TextMessage(content=updated_task, source="user")],
            cancellation_token=CancellationToken(),
        )
        set_status_ok()
        return f"I've completed the task. Result: {chat_result.chat_message.content}"
    except Exception as e:
        set_status_error(e)
        return f"An error occurred inside dex_agent: {str(e)}"
