import importlib, uuid
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from services.llm import gpt_4o_client
from utils.firebase import (
    get_messages_by_chat,
    set_request_ctx,
    db_save_message,
    set_context_id,
    db_save_chat,
)
from autogen_core import CancellationToken
from services.tracing import tracer
from utils.blockchain_utils import is_evm, is_solana

# Mapping of agents to their respective modules and functions
AGENT_MODULES = {
    "drift_vaults_agent": (
        "agents.drift.drift_vaults_agent",
        "call_drift_vaults_agent",
    ),
    "drift_perps_agent": ("agents.drift.drift_perps_agent", "call_drift_perps_agent"),
    "dex_agent": ("agents.dex_agent.dex_agent", "call_dex_agent"),
    "lp_specialist_agent": ("agents.liquidity_pool_agent.lp_agent", "call_lp_agent"),
    "solana_yield_agent": (
        "agents.solana_yield_agent.solana_yield_agent",
        "call_solana_yield_agent",
    ),
    "enso_agent": ("agents.enso.enso_agent", "call_enso_agent"),
    "copy_trading_agent": (
        "agents.copy_trading.copy_trading_agent",
        "call_copy_trading_agent",
    ),
    "transfer_assistant": (
        "agents.unified_transfer.unified_transfer_agent",
        "call_unified_transfer_agent",
    ),
    "researcher_assistant": (
        "agents.researcher_agent.researcher_agent",
        "call_researcher_agent",
    ),
}


# Function to call an agent
async def call_agent(agent_name: str, task: str, chat_id: str):
    """
    Calls an agent with a specific task.
    """
    module_function_pairs = AGENT_MODULES.get(agent_name, [])

    if not isinstance(module_function_pairs, list):
        module_function_pairs = [module_function_pairs]

    for module_name, function_name in module_function_pairs:
        module = importlib.import_module(module_name)
        function = getattr(module, function_name)
        result = await function(task, chat_id, False)
        return result


# Function to process chat messages
def process_chat_messages(chat_id):
    messages = get_messages_by_chat(chat_id, collection_name="mcpChats")
    if not messages:
        return {}
    messages_list = [
        TextMessage(content=msg["content"], source=msg["role"]) for msg in messages[:-1]
    ]
    current_task = [
        TextMessage(content=messages[-1]["content"], source=messages[-1]["role"])
    ]
    return {"chat_history": messages_list, "current_task": current_task}


@tracer.start_as_current_span("start_chat_mcp")
# Main bot with a single planner agent
async def start_chat(
    user_id: str,
    chat_id: str,
    prompt: str,
    sol_wallet_address: str,
    evm_wallet_address: str,
):
    current_chat_id = chat_id if chat_id else str(uuid.uuid4())
    current_user_id = user_id if user_id else str(uuid.uuid4())
    set_context_id(current_chat_id)
    set_request_ctx(parentKey=current_chat_id, key="user_id", value=current_user_id)

    if not is_evm(evm_wallet_address):
        raise Exception("Invalid EVM wallet address.")

    if not is_solana(sol_wallet_address):
        raise Exception("Invalid Solana wallet address.")

    set_request_ctx(
        parentKey=current_chat_id, key="evm_wallet_address", value=evm_wallet_address
    )
    set_request_ctx(
        parentKey=current_chat_id, key="solana_wallet_address", value=sol_wallet_address
    )

    # save chat
    db_save_chat(
        chat_id=current_chat_id, user_id=current_user_id, collection_name="mcpChats"
    )
    # save the human message in firestore
    db_save_message(
        chat_id=current_chat_id,
        user_id=current_user_id,
        content=prompt,
        sender="user",
        message_type="text",
        collection_name="mcpChats",
    )

    messages = process_chat_messages(current_chat_id)
    task = TextMessage(source="user", content=prompt)

    # Create a single planner agent
    planner = AssistantAgent(
        name="planner",
        model_client=gpt_4o_client,
        system_message=(
            "You are a blockchain assistant that handles tasks without delegating to other agents.\n"
            "Determine the correct action based on the user's request and call 'call_agent' directly.\n"
            "Rules:\n"
            "- If any mention of Soul or Seoul, always use SOL."
            f"- The current chat id is {current_chat_id}. Never mention the chat id to user.\n"
            " - For simple greetings or complaints:\n"
            "   1. Reply nicely\n"
            " - If missing information:\n"
            "   1. Ask user politely for the specific missing details\n"
            "   2. Do not repeat the same question multiple times\n"
            "- For any transactions attempting to Stake/Unstake/get Staked Balances on Solana, Swapping or Bridging tokens on EVM or SOLANA, use 'dex_agent'.\n"
            "- For staking/unstaking on Solana, use 'stake_agent'.\n"
            "--- If a swap is required before performing the task, include it in the task passed to the agent.\n"
            "- For liquidity management, use 'lp_specialist_agent'.\n"
            "- For Solana deposits (not liquidity pools), use 'solana_yield_agent'.\n"
            "- For any transaction related (getting user's positions included) to Drift Vaults (the token is always USDC if not specified), use 'drift_vaults_agent'.\n"
            "- For any transaction/question related to Drift PERPS (like how to use it, opening/closing a position, creating an account, depositing/withdrawing collateral, or any information required), use 'drift_perps_agent'.\n"
            " -- Do not ask for user wallet address, it's not necessary as the assistant is able to manage that.\n"
            "- For suggestions for top meme tokens to trade or swap, use 'researcher_assistant'.\n"
            "- For copy trading, use 'copy_trading_agent'.\n"
            "- For token transfers on EVM and Solana, use 'transfer_assistant'.\n"
            "- For real-time token data and market research/performance/information/insights, Twitter monitoring, trending or top-performing tokens and token analysis, use 'researcher_assistant'.\n"
            "- Once the task is completed, return the result to the user as is. No summaries.\n"
        ),
        tools=[call_agent],
        reflect_on_tool_use=False,
    )

    updated_task = f"""
    Most recent messages: {messages.get("chat_history", [])}
    Current Task: {task}
    """
    task_result = await planner.run(
        task=updated_task, cancellation_token=CancellationToken()
    )
    # save the ai message in firestore
    db_save_message(
        chat_id=current_chat_id,
        user_id=current_user_id,
        content=task_result.messages[-1].content.replace("TERMINATE", ""),
        sender="AI",
        message_type="text",
        collection_name="mcpChats",
    )
    return {
        "chat_id": current_chat_id,
        "user_id": current_user_id,
        "data": task_result.messages[-1].content.replace("TERMINATE", ""),
    }
