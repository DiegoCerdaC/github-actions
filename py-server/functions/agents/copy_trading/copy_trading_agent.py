from typing import Annotated
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from services.llm import gpt_4o_client
from utils.firebase import get_request_ctx, save_agent_thought
import services.analytics as analytics
from agents.copy_trading.copy_trading_functions import (
    copy_trading,
    get_swaps_by_wallet_address,
)
from agents.dex_agent.dex_agent import call_dex_agent
from services.tracing import set_status_ok, set_status_error, tracer, set_attributes


@tracer.start_as_current_span("copy_trading_agent")
async def call_copy_trading_agent(
    task: str, chat_id: str, use_frontend_quoting: bool = True
) -> Annotated[str, "The chat history summary of the copy trading agent."]:
    """
    Copy trade swaps from a tracked wallet to user's wallet.
    Examples:
    - I want to copy the sells/buys of the wallet xxxxx on Solana
    - I want to make copy trading of the wallet yyyyy on Solana
    Args:
        task (str): Query describing copy trading task (e.g. "Copy trades from wallet xxxxx")
        chat_id (str): the current chat id,
    Returns:
        str: Agent response with results or errors
    """
    analytics.increment_agent_used("copy_trading", chat_id)
    set_attributes(
        {"chat_id": chat_id, "task": task, "use_frontend_quoting": use_frontend_quoting}
    )

    wallet_address = get_request_ctx(chat_id, "solana_wallet_address")

    save_agent_thought(
        chat_id=chat_id,
        thought="Processing your copy trading request...",
    )

    if wallet_address is None:
        raise Exception("No wallet address found.")

    copy_trading_agent = AssistantAgent(
        name="copy_trading_agent",
        system_message=(
            "You are a copy trading expert that helps users copy trades from other wallets. "
            "Main Task:\n"
            "Copy trading activity by gathering info and executing swaps according to these guidelines. Ensure all operations match user intent and are clearly communicated. "
            "Ensure that the wallet address has no spaces or special characters, such as a trailing dot or dash.\n"
            f"And use_frontend_quoting is ALWAYS {use_frontend_quoting}.\n"
            "Best Practices:\n"
            "- Ensure sale values cover purchase costs\n"
            "- Stay within available token balances\n"
            "- Use clear, specific prompts for swaps\n"
            "- Split large swaps proportionally (e.g. $100 SOL sale into $60 USDT + $40 USDC)"
        ),
        model_client=gpt_4o_client,
        reflect_on_tool_use=True,
        tools=[
            copy_trading,
            get_swaps_by_wallet_address,
            call_dex_agent,
        ],
    )

    updated_task = f"""
    The user requested the following task: '{task}'.
    Their wallet address is: '{wallet_address}'.
    Current chat id is: {chat_id}
    """

    try:
        chat_result = await copy_trading_agent.on_messages(
            messages=[TextMessage(content=updated_task, source="user")],
            cancellation_token=CancellationToken(),
        )
        set_status_ok()
        return chat_result.chat_message.content
    except Exception as e:
        set_status_error(e)
        return f"An error occurred: {str(e)}"
