from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from utils.firebase import get_request_ctx
import services.analytics as analytics

from agents.solana_yield_agent.lulo_yield_functions import (
    get_user_deposits,
    generate_deposit_transaction,
    generate_withdrawal_transaction,
)
from services.llm import gpt_4o_client
from services.tracing import set_status_ok, set_status_error, tracer, set_attributes


@tracer.start_as_current_span("solana_yield_agent")
async def call_solana_yield_agent(
    task: str, chat_id: str, use_frontend_quoting: bool = True
) -> str:
    """
    Manages yield opportunities on Solana via Lulo Protocol through depositing/withdrawing on yield tokens.
    Examples:
    - Deposit 104 USDC
    - I want to deposit 200 USDT on Solana
    - I want information about my deposits on Lulo
    - I want to know my deposits on Solana
    - Deposit 15 USDT on SOLANA
    Args:
        task (str): Staking instruction with amount and optional pool
        chat_id (str): the current chat id

    Response can be:
    - Message to confirm that the transactions was generated and the user needs to CONFIRM.
    - Message to notify the user that his balances is not enough and ask the user which token swap from to make the deposit.

    """
    analytics.increment_agent_used("solana_yield", chat_id)
    set_attributes(
        {"chat_id": chat_id, "task": task, "use_frontend_quoting": use_frontend_quoting}
    )

    wallet_address = get_request_ctx(chat_id, "solana_wallet_address")
    if wallet_address is None:
        raise Exception("No wallet address found. Provide a valid wallet address.")

    yield_agent = AssistantAgent(
        name="yield_agent",
        model_client=gpt_4o_client,
        tools=[
            get_user_deposits,
            generate_deposit_transaction,
            generate_withdrawal_transaction,
        ],
        system_message=(
            "Yield Agent for Lulo Protocol on Solana.\n"
            "If the user asks about yield options, best yields, or how to earn yield on Solana (e.g., prompts like 'What yield options are available', 'I would like to know the best yields on solana', 'I want to yield earn', etc), call the 'generate_deposit_transaction' tool with default values and use_frontend_quoting set to True.\n"
            "If user wants to know about their account information or deposits and yield rates, use get_user_deposits.\n"
            "If user wants to deposit, use generate_deposit_transaction.\n"
            "If user wants to withdraw, use generate_withdrawal_transaction.\n"
            "If the response indicates a swap is needed, ask the user to specify the token to swap from to cover the required amount in dollars for the deposit and wait for a response. Always specify the amount in dollars needed in the response in this case."
        ),
    )

    updated_task = f"""
    The user wants to do the following task: {task}
    User wallet address is : {wallet_address}
    Current chat is {chat_id}.
    And use_frontend_quoting is ALWAYS {use_frontend_quoting}.
    """

    try:
        chat_result = await yield_agent.on_messages(
            messages=[TextMessage(content=updated_task, source="user")],
            cancellation_token=CancellationToken(),
        )

        set_status_ok()
        return f"I've completed the task. Result: {chat_result.chat_message.content}"

    except Exception as e:
        set_status_error(e)
        return f"An error occurred: {str(e)}"
