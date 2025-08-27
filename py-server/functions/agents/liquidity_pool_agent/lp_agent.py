import services.analytics as analytics
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from services.llm import gpt_4o_client
from utils.firebase import get_request_ctx
from agents.liquidity_pool_agent.lp_specialist_functions import (
    display_user_positions_for_pool_term,
    search_for_pool,
    deposit_liquidity,
    withdraw_liquidity,
    get_user_positions_for_pool_term,
    get_all_active_positions_on_meteora,
    relocate_user_liquidity_to_highest_apy_pool,
    claim_fees_and_reinvest,
    build_claim_swap_fees_tx,
)
from services.tracing import set_status_ok, set_status_error, tracer, set_attributes


@tracer.start_as_current_span("lp_agent")
async def call_lp_agent(
    task: str, chat_id: str, use_frontend_quoting: bool = True
) -> str:
    """
    Assistant that helps the user with managing their liquidity pools.
    It can handle deposits, withdrawals, relocations, and claiming swap fees.

    Examples:
    - I want to get information about my pool TRUMP-SOL
    - Deposit 0.02 SOL on the pool SOL-USDC
    - I want to withdraw 100% of the liquidity I have on the pool GRIFT-USDC
    - Claim the fees from the pool SOL-TRUMP
    - Relocate the liquidity I have on SOL-USDC to the highest APY pool on the same pair
    - I want to claim and reinvest the fees from the pool SOL-USDC

    Args:
    - task (str): The task to be executed (what the user asked for)
    - chat_id (str): the current chat id

    # Returns:
    - str: The result of the task execution or error message
    """
    analytics.increment_agent_used("lp_agent", chat_id)
    set_attributes(
        {"chat_id": chat_id, "task": task, "use_frontend_quoting": use_frontend_quoting}
    )
    lp_agent = AssistantAgent(
        name="lp_agent",
        system_message=(
            "You are a liquidity pool management assistant.\n"
            f"use_frontend_quoting is ALWAYS {use_frontend_quoting}.\n"
            "- Get information/performance about user positions on a pool (user specifies token pair), use display_user_positions_for_pool_term.\n"
            "- Get list/information of ALL user active LPs/Positions on Meteora, use get_all_active_positions_on_meteora.\n"
            "- Find pool addresses for token pairs, use search_for_pool.\n"
            "- Deposit into a specific pool, use deposit_liquidity.\n"
            "- Get pool info when the user wants to withdraw/claim without specifying the pool address, use get_user_positions_for_pool_term.\n"
            "- Withdraw from a pool, use withdraw_liquidity (type is always 'all' unless the user specifies extrictly to be 'single')\n"
            "- Claim fees (without the user asking to reinvest), use build_claim_swap_fees_tx\n"
            "- Reinvest generated fees, use claim_fees_and_reinvest\n"
            "- Move liquidity to highest APY pool, use relocate_user_liquidity_to_highest_apy_pool\n"
            "For pool selection: Ask user to choose from displayed list without additional info.\n"
        ),
        model_client=gpt_4o_client,
        reflect_on_tool_use=False,
        tools=[
            display_user_positions_for_pool_term,
            search_for_pool,
            deposit_liquidity,
            get_user_positions_for_pool_term,
            get_all_active_positions_on_meteora,
            withdraw_liquidity,
            relocate_user_liquidity_to_highest_apy_pool,
            build_claim_swap_fees_tx,
            claim_fees_and_reinvest,
        ],
    )

    solana_wallet_address = get_request_ctx(chat_id, "solana_wallet_address")

    task_with_wallet = (
        f"The user asked for this task: {task}. "
        f"User Solana Wallet Address: {solana_wallet_address}. "
        f"Current chat is: {chat_id}."
    )

    try:
        chat_result = await lp_agent.on_messages(
            messages=[TextMessage(content=task_with_wallet, source="user")],
            cancellation_token=CancellationToken(),
        )
        set_status_ok()
        return chat_result.chat_message.content
    except Exception as e:
        set_status_error(e)
        return f"An error occurred: {str(e)}"
