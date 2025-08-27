from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from services.llm import gpt_4o_client
from utils.firebase import get_request_ctx
from agents.unified_transfer.transfer_functions import (
    create_evm_transfer,
    create_solana_transfer,
)
from services.tracing import set_status_ok, set_status_error, tracer, set_attributes
import services.analytics as analytics


@tracer.start_as_current_span("unified_transfer_agent")
async def call_unified_transfer_agent(
    task: str, chat_id: str, use_frontend_quoting: bool = True
) -> str:
    """
    Executes crypto transfers on EVM/Solana chains and bridges USDC between them.
    Examples:
    - transfer 1 SOL to xxxx on SOLANA
    - transfer 1 USDC to xxxx on Polygon
    - transfer 1000 GRIFT to xxxx on Solana
    Args:
        task (str): Transfer request with chain, token, amount and recipient
        chat_id (str): The current chat id
    Returns:
        str: Success/failure response with transaction details
    """
    analytics.increment_agent_used("unified_transfer", chat_id)
    set_attributes(
        {"chat_id": chat_id, "task": task, "use_frontend_quoting": use_frontend_quoting}
    )
    # Get wallet addresses from context
    evm_wallet_address = get_request_ctx(chat_id, "evm_wallet_address")
    solana_wallet_address = get_request_ctx(chat_id, "solana_wallet_address")

    transfer_agent = AssistantAgent(
        name="transfer_agent",
        system_message=(
            "Crypto transfer assistant for EVM and Solana chains.\n"
            "DO NOT JUDGE THE TOKEN NAME, just transfer the token. "
            "Users request transfers on SOLANA, use 'create_solana_transfer'. "
            "For EVM transfers, use 'create_evm_transfer'. "
            "Amount should be greater than 0 (even small amounts are allowed, but not lower or equal to 0). "
            "If the user doesn't specify the chain where to perform the transfer, ask for it, do not assume it. "
            "Wallets: "
            f"EVM: {evm_wallet_address}, Solana: {solana_wallet_address}. "
            f"Current Chat ID: {chat_id}. And use_frontend_quoting is ALWAYS {use_frontend_quoting}.\n"
            "Error handling:\n"
            "-Check balances\n"
            "-Validate addresses\n"
            "-Verify token/chain support"
        ),
        model_client=gpt_4o_client,
        tools=[create_evm_transfer, create_solana_transfer],
        reflect_on_tool_use=False,
    )

    try:
        chat_result = await transfer_agent.on_messages(
            messages=[TextMessage(content=task, source="user")],
            cancellation_token=CancellationToken(),
        )
        set_status_ok()
        return chat_result.chat_message.content
    except Exception as e:
        set_status_error(e)
        return f"An error occurred: {str(e)}"
