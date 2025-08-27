from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
import services.analytics as analytics
from agents.drift.drift_perps_information import drift_perps_explanation
from agents.drift.drift_functions import (
    create_drift_account,
    deposit_or_withdraw_collateral,
    open_perps_position,
    close_perps_position,
    get_user_active_orders,
    close_order_by_id_and_symbol,
    close_all_active_orders,
    get_user_active_positions,
    get_drift_perps_account_info,
    get_perps_markets,
)
from services.llm import gpt_4o_client
from services.tracing import set_status_ok, set_status_error, tracer, set_attributes


def get_drift_perps_information():
    """
    Returns information about how Drift Perps works.
    Includes examples of how to use the tools and how to interact with the agent.
    It explains also the steps to start using this tool.
    """
    return drift_perps_explanation


@tracer.start_as_current_span("drift_perps_agent")
async def call_drift_perps_agent(
    task: str, chat_id: str, use_frontend_quoting: bool = True
) -> str:
    """
    Manages user PERPS positions on DRIFT Protocol.
    Examples:
    - I want to add 10 USDC as Collateral on my DRIFT account
    - I want to withdraw 10 USDC from my DRIFT account
    - I want to open a LONG position on JUP with 20 JUP
    - Open a short market order on SOL with 100 SOL
    - Close 100% of the LONG Position I have on JUP
    - I want to cancell all my active orders on Drift Perps
    - How much can I withdraw from my drift perps account?
    - I want to know how much collateral I have in my drift perps account.

    Response can be:
    - Message to confirm that the transactions was generated and the user needs to CONFIRM.
    - Message to notify the user about any error that occurred and ask him for more information or try again.

    """
    analytics.increment_agent_used("drift_perps", chat_id)
    set_attributes(
        {
            "chat_id": chat_id,
            "task": task,
            "use_frontend_quoting": use_frontend_quoting,
        }
    )

    drift_perps_agent = AssistantAgent(
        name="drift_perps_agent",
        model_client=gpt_4o_client,
        tools=[
            create_drift_account,
            deposit_or_withdraw_collateral,
            open_perps_position,
            close_perps_position,
            get_user_active_orders,
            close_order_by_id_and_symbol,
            close_all_active_orders,
            get_user_active_positions,
            get_drift_perps_information,
            get_drift_perps_account_info,
            get_perps_markets,
        ],
        system_message=(
            "You're a helpful assistant that helps users manage their PERPS positions on DRIFT Protocol.\n"
            "Handle PERPS transactions on DRIFT Protocol using these functions:\n\n"
            "1. create_drift_account: Use when user wants to create a new DRIFT account.\n"
            "2. get_drift_perps_account_info: Use when user wants to get information about their drift perps account or wants to withdraw but doesn't know how much he can withdraw.\n"
            "3. deposit_or_withdraw_collateral: Use when user wants to DEPOSIT (not create) or withdraw collateral.\n"
            "4. open_perps_position: Use when user wants to open a new PERPS position.\n"
            "5. close_perps_position: Use when user wants to close a PERPS position.\n"
            "6. get_user_active_orders: Use when user wants to get their active orders, or if the user wants to cancel an orden but doesn't know the order id.\n"
            "7. close_order_by_id_and_symbol: Use when user wants to cancel an order by providing the order id and the symbol of the market.\n"
            "8. close_all_active_orders: Use when user wants to cancel ALL their active orders.\n"
            "9. get_user_active_positions: Use when user wants to get their active positions.\n"
            "10. get_drift_perps_information: Use when user wants to get information about Drift Perps, or if the user doesn't know how to use the tool, or is asking any question related to Drift Perps. Be briefly when explaining.\n"
            "11. get_perps_markets: Use when user wants to get the available perps markets, or he wants to open an order/position but doesn't know the available markets.\n"
            "If any required parameter is missing, ask the user to specify it (don't assume anything).\n"
            "Considerations: it's not necessary to ask if the user has a drift account when calling any tool, because each tool will do that check and handle this.\n"
            "Error handling: If the user doesn't have a drift account, ask him if he needs help to create one and help him to create one."
        ),
    )

    updated_task = f"""
    The user wants to do the following task: {task}
    Current chat is {chat_id}.
    And use_frontend_quoting is ALWAYS {use_frontend_quoting} when using any tool.
    """
    try:
        chat_result = await drift_perps_agent.on_messages(
            messages=[TextMessage(content=updated_task, source="user")],
            cancellation_token=CancellationToken(),
        )
        set_status_ok()
        return f"I've completed the task. Result: {chat_result.chat_message.content}"

    except Exception as e:
        set_status_error(e)
        return f"An error occurred: {str(e)}"
