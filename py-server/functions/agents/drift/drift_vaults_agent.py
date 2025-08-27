from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
import services.analytics as analytics
from agents.drift.drift_functions import (
    generate_drift_vault_transaction,
    get_user_vaults,
    select_vault_to_withdraw_from,
    select_vault_to_deposit_to,
)
from services.llm import gpt_4o_client
from services.tracing import set_status_ok, set_status_error, tracer, set_attributes
from utils.firebase import save_agent_thought


@tracer.start_as_current_span("drift_vaults_agent")
async def call_drift_vaults_agent(
    task: str, chat_id: str, use_frontend_quoting: bool = True
) -> str:
    """
    Manages user deposits on DRIFT Vaults for USDC Token.
    Examples:
    - I want to deposit 100 USDC on DRIFT Vault
    - I want to deposit 200 USDC on DRIFT Protocol
    - Please I want to request a withdraw of 100 USDC from DRIFT
    - I want to initiate the withdraw process of 40 USDC from DRIFT
    - Add 150 USDC on DRIFT
    - Withdraw 100 USDC from DRIFT
    - I want to take out 100 USDC from DRIFT vaults

    Response can be:
    - Message to confirm that the transactions was generated and the user needs to CONFIRM.
    - Message to notify the user about any error that occurred and ask him for more information or try again.
    """
    analytics.increment_agent_used("drift_vaults", chat_id)
    set_attributes(
        {
            "chat_id": chat_id,
            "task": task,
            "use_frontend_quoting": use_frontend_quoting,
        }
    )

    drift_vaults_agent = AssistantAgent(
        name="drift_vaults_agent",
        model_client=gpt_4o_client,
        tools=[
            generate_drift_vault_transaction,
            get_user_vaults,
            select_vault_to_withdraw_from,
            select_vault_to_deposit_to,
        ],
        system_message=(
            "Drift Agent for DRIFT Vaults Protocol.\n"
            "Handle USDC transactions on DRIFT Vaults Protocol using these functions:\n\n"
            "1. get_user_vaults: Use ONLY when user asks about their vaults, balances, or performance.\n"
            "2. select_vault_to_withdraw_from: Use ONLY when user wants to withdraw/request withdrawal but hasn't specified a vault.\n"
            "3. select_vault_to_deposit_to: Use ONLY when user wants to deposit USDC but hasn't specified a vault.\n"
            "4. generate_drift_vault_transaction: Use for all transactions with these types:\n"
            "   - 'deposit': Add USDC (requires amount)\n"
            "   - 'request_withdraw': Initiate withdrawal (requires amount or percentage to request)\n"
            "   - 'withdraw': Complete withdrawal (no amount needed)\n\n"
            "Only USDC is supported.\n"
            "If any required parameter is missing, ask the user to specify it (don't assume anything)."
        ),
    )

    updated_task = f"""
    The user wants to do the following task: {task}
    Current chat is {chat_id}.
    And use_frontend_quoting is ALWAYS {use_frontend_quoting} when using any tool.
    """
    try:
        chat_result = await drift_vaults_agent.on_messages(
            messages=[TextMessage(content=updated_task, source="user")],
            cancellation_token=CancellationToken(),
        )
        set_status_ok()
        return f"I've completed the task. Result: {chat_result.chat_message.content}"

    except Exception as e:
        set_status_error(e)
        error_message = f"An error occurred: {str(e)}"
        save_agent_thought(
            chat_id=chat_id,
            thought=f"Error processing request: {str(e)}",
            isFinalThought=True,
        )
        return error_message
