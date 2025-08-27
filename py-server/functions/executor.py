import importlib
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import TextMessage, ModelClientStreamingChunkEvent
from services.llm import gpt_4o_client
from utils.firebase import (
    get_messages_by_chat,
    get_user_wallets,
    set_request_ctx,
    update_message,
    create_message_doc_id,
    set_context_id,
    save_agent_thought,
)
from services.voice import encode_audio_to_base64, generate_speech_from_text
from autogen_core import CancellationToken
from services.memory_service import MemoryService
from utils.blockchain_utils import is_evm, is_solana
import services.analytics as analytics

import json

from services.tracing import tracer, set_status_error, set_status_ok, set_attributes


# Mapping of agents to their respective modules and functions
AGENT_MODULES = {
    "drift_vaults_agent": (
        "agents.drift.drift_vaults_agent",
        "call_drift_vaults_agent",
    ),
    "drift_perps_agent": ("agents.drift.drift_perps_agent", "call_drift_perps_agent"),
    "scheduler_agent": (
        "agents.scheduler_agent.scheduler_agent",
        "call_scheduler_agent",
    ),
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
    "orbit_rag_agent": (
        "agents.orbit_rag_agent.orbit_rag_agent",
        "call_orbit_rag_agent",
    ),
    "liquidation_agent": (
        "agents.liquidation_agent.liquidation_agent",
        "call_liquidation_agent",
    ),
}


# Function to call an agent
async def call_agent(agent_name: str, task: str, chat_id: str):
    """
    Calls an agent with a specific task.
    """
    try:
        module_function_pairs = AGENT_MODULES.get(agent_name, [])

        if not isinstance(module_function_pairs, list):
            module_function_pairs = [module_function_pairs]

        save_agent_thought(
            chat_id=chat_id,
            thought="Analyzing your request...",
        )

        for module_name, function_name in module_function_pairs:
            module = importlib.import_module(module_name)
            function = getattr(module, function_name)
            result = await function(task, chat_id, True)
            return result
    except Exception as e:
        set_status_error(e)
        raise e


# Function to process chat messages
def process_chat_messages(chat_id):
    messages = get_messages_by_chat(chat_id)
    if not messages:
        return []
    messages_list = [
        TextMessage(content=msg["content"], source=msg["role"]) for msg in messages[:-1]
    ]
    current_task = [
        TextMessage(content=messages[-1]["content"], source=messages[-1]["role"])
    ]
    return {"chat_history": messages_list, "current_task": current_task}


# Main bot with a single planner agent
@tracer.start_as_current_span("start_bot")
async def start_bot(
    user_id: str,
    chat_id: str,
    integrator_id: str,
    summary: str,
    use_voice: bool = False,
):
    set_attributes(
        {
            "chat_id": chat_id,
            "user_id": user_id,
            "integrator_id": integrator_id,
            "use_voice": use_voice,
            "summary": summary,
        }
    )
    user_wallets = get_user_wallets(user_id)
    if not user_wallets:
        set_status_error("No wallets found.")
        return "No wallets found."
    evm_wallet_address = user_wallets.get("EVM", {}).get("wallet_address")
    sol_wallet_address = user_wallets.get("SOLANA", {}).get("wallet_address")

    if not is_evm(evm_wallet_address):
        raise Exception("Invalid EVM wallet address.")

    if not is_solana(sol_wallet_address):
        raise Exception("Invalid Solana wallet address.")

    set_context_id(chat_id)
    set_request_ctx(parentKey=chat_id, key="user_id", value=user_id)
    set_request_ctx(
        parentKey=chat_id, key="evm_wallet_address", value=evm_wallet_address
    )
    set_request_ctx(
        parentKey=chat_id, key="solana_wallet_address", value=sol_wallet_address
    )

    messages = process_chat_messages(chat_id)
    task = messages.get("current_task")
    current_message = task[0].content if task else ""

    # Increase analytics count for 'total_messages'
    analytics.increment_message_count(chat_id)

    # Initialize memory service and extract information
    memory_service = MemoryService()

    # Get memory context for the agent
    memory_context = await memory_service.get_agent_memory_context(
        user_id=user_id, task=current_message
    )

    # Convert memory context to JSON string
    memory_context_json = json.dumps(memory_context)

    # Create a single planner agent with enhanced memory context
    planner = AssistantAgent(
        name="planner",
        model_client=gpt_4o_client,
        system_message=(
            "You are a blockchain assistant that handles tasks without delegating to other agents.\n"
            "Determine the correct action based on the user's request and call 'call_agent' directly.\n"
            "If user mentions a function or tool, call it directly. Do not ask for confirmation or more details but don't mention the tool name on the response.\n"
            "Rules:\n"
            "- If any mention of Soul or Seoul, always use SOL."
            f"- The current chat id is {chat_id}. Never mention the chat id to user.\n"
            "- Never modify chain names. Use them exactly as provided by the user (e.g., if user says BINANCE, use BINANCE, not Binance Smart Chain).\n"
            " - For simple greetings or complaints:\n"
            "   1. Reply nicely\n"
            " - If missing information:\n"
            "   1. Ask user politely for the specific missing details\n"
            "   2. Do not repeat the same question multiple times\n"
            "- For liquidation of assets (liquidate all assets, convert all tokens, consolidate portfolio, liquidate everything), use 'liquidation_agent'.\n"
            "- For individual swaps, bridges, and staking operations (but NOT liquidation of all assets), use 'dex_agent'.\n"
            "--- If a swap is required before performing the task, include it in the task passed to the agent.\n"
            "- For any task related to scheduled taks, use 'scheduler_agent'.\n"
            "-- Do not call any other assistant when asking for scheduled tasks. Just use 'scheduler_agent' on 'call_agent' tool.\n"
            "- For any transaction related (getting user's positions included) to Drift Vaults (the token is always USDC if not specified), use 'drift_vaults_agent'.\n"
            "- For any transaction/question related to Drift PERPS (like how to use it, opening/closing a position, creating an account, depositing/withdrawing collateral, or any information required), use 'drift_perps_agent'.\n"
            " -- Do not ask for user wallet address, it's not necessary as the assistant is able to manage that.\n"
            "- For liquidity management, use 'lp_specialist_agent'.\n"
            "- For Solana deposits (not liquidity pools), use 'solana_yield_agent'.\n"
            "- For EVM Deposits or Withdrawals, use 'enso_agent'. No needed to specify the chain. The agent will handle every case.\n"
            "- If the user wants to make a deposit/withdraw/get yield/win money but doesn't specify the chain, assume it's EVM and call the 'enso_agent'.\n"
            "- For suggestions for top meme tokens to trade or swap, use 'researcher_assistant'.\n"
            "- For copy trading, use 'copy_trading_agent'.\n"
            "- For token transfers on EVM and Solana, use 'transfer_assistant'.\n"
            "- For portfolio analysis, performance tracking, or questions like 'how is my portfolio doing?', use 'researcher_assistant'.\n"
            "- For questions about Orbit's company, mission, vision, tokenomics, roadmap, founders, supported protocols/chains/networks/tokens, or general inquiries about 'what is Orbit?' and 'what is the role of the token?', use 'orbit_rag_agent'.\n"
            "- For real-time token data and market research/performance/information/insights, Twitter monitoring, trending or top-performing tokens/dexs/protocols/pools and token analysis, use 'researcher_assistant'.\n"
            "- Once the task is completed, return the result to the user.\n"
            "- If the user wants to get a token but only sends the token symbol or address, check the context and try to find the token metadata, if you fail, ask for the chain name.\n"
            "- If the user wants a financial advice/recommendation related to a token, trade, etc, always call the corresponding agent, and attach with the response a disclaimer that the response is not financial advice, and that the user should do their own research. But always call the corresponding agent.\n"
            "- Error handling: if any error occurs, or an assistant returns an error, explain very briefly to the user, ask him to try again changing the parameters or what he requested (if needed), or to try again later. Asking for more details is not an error.\n"
        ),
        tools=[call_agent],
        reflect_on_tool_use=True,
        model_client_stream=True,
    )

    updated_task = f"""
    Summary of Overall Chat History: {summary}
    Most recent messages: {messages.get("chat_history", [])}
    Current Task: {task}
    """
    # create message doc id, so all streams and voice will be added to the same message doc
    message_id = create_message_doc_id(chat_id=chat_id)
    set_attributes(
        {
            "chat_id": chat_id,
            "user_id": user_id,
            "integrator_id": integrator_id,
            "use_voice": use_voice,
        }
    )
    try:
        # stream the messages from planner
        async for message in planner.on_messages_stream(
            messages=[
                TextMessage(content=updated_task, source="user"),
                TextMessage(content=memory_context_json, source="assistant"),
            ],
            cancellation_token=CancellationToken(),
        ):
            # if message is a type of message chunk, write to message doc
            if isinstance(message, ModelClientStreamingChunkEvent):
                await update_message(
                    chat_id=chat_id,
                    user_id=user_id,
                    message_id=message_id,
                    data={
                        "content": message.content.replace("TERMINATE", ""),
                        "sender": "AI",
                        "voiceContent": "",
                        "useVoice": False,
                        "messageType": "text",
                    },
                )
            # then we get final response, which has all the message chunks concatenated together
            # use that to create the voice message
            elif isinstance(message, Response):
                # save the user input and output
                await memory_service.store_message_memory(
                    user_id=user_id,
                    content=task[0].content,
                    agent_response=message.chat_message.content.replace(
                        "TERMINATE", ""
                    ),
                    chat_id=chat_id,
                )
                if use_voice:
                    voice_result = generate_speech_from_text(
                        text=message.chat_message.content.replace("TERMINATE", "")
                    )
                    encoded_voice = encode_audio_to_base64(voice_result)
                    await update_message(
                        chat_id=chat_id,
                        user_id=user_id,
                        message_id=message_id,
                        data={
                            "content": "",
                            "sender": "AI",
                            "voiceContent": encoded_voice,
                            "useVoice": True,
                            "messageType": "text",
                        },
                    )
        set_status_ok()

    except Exception as e:
        set_status_error(e)
        raise e

    return
