import importlib, uuid, ast, json
from pydantic import BaseModel
from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from utils.firebase import set_request_ctx, set_context_id
from autogen_core import CancellationToken
from services.tracing import tracer
from config import OPENAI_API_KEY
from utils.automated_transaction import (
    perform_automated_transaction,
    TransactionData
)

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
    "transfer_assistant": (
        "agents.unified_transfer.unified_transfer_agent",
        "call_unified_transfer_agent",
    ),
}


# Function to call an agent
# with `use_frontend_quoting` to be `false`
async def call_agent(agent_name: str, task: str, chat_id: str):
    """
    Calls an agent with a specific task.
    """
    try:
        module_function_pairs = AGENT_MODULES.get(agent_name, [])

        if not isinstance(module_function_pairs, list):
            module_function_pairs = [module_function_pairs]

        for module_name, function_name in module_function_pairs:
            module = importlib.import_module(module_name)
            function = getattr(module, function_name)
            result = await function(task, chat_id, False)
            return result
    except Exception as e:
        raise e


def safe_parse(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(text)
        except Exception as e:
            raise ValueError(f"Couln't parse the content. Error: {e}")


class AgentResponse(BaseModel):
    """The expected structured response to return.
    - message: the overall summary of the task
    - transaction: the full transaction dictionary
    """
    message: str
    transaction: TransactionData

    class Config:
        extra = "forbid"


@tracer.start_as_current_span("start_automated_executor")
# Main bot with a single planner agent
async def start_automated_executor(
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
    set_request_ctx(parentKey=current_chat_id, key="evm_wallet_address", value=evm_wallet_address)
    set_request_ctx(parentKey=current_chat_id, key="solana_wallet_address", value=sol_wallet_address)
    task = TextMessage(source="user", content=prompt)

    llm_with_structured_output = OpenAIChatCompletionClient(
        model="gpt-4o",
        api_key=OPENAI_API_KEY,
        temperature=0.0,
        seed=None,
        response_format=AgentResponse,
    )

    automated_executor = AssistantAgent(
        name="automated_executor",
        model_client=llm_with_structured_output,
        system_message=(
            "You are a blockchain assistant that handles tasks without delegating to other agents.\n"
            "Determine the correct action based on the user's request and call 'call_agent' directly.\n"
            "If user mentions a function or tool, call it directly. Do not ask for confirmation or more details but don't mention the tool name on the response.\n"
            "Rules:\n"
            "- If any mention of Soul or Seoul, always use SOL."
            f"- The current chat id is {chat_id}. Never mention the chat id to user.\n"
            "- Never modify chain names. Use them exactly as provided by the user (e.g., if user says BINANCE, use BINANCE, not Binance Smart Chain).\n"
            " - If missing information:\n"
            "   1. Ask user politely for the specific missing details\n"
            "   2. Do not repeat the same question multiple times\n"
            "- For any transactions attempting to Stake/Unstake/get Staked Balances on Solana, Swapping or Bridging tokens on EVM or SOLANA, use 'dex_agent'.\n"
            "--- If a swap is required before performing the task, include it in the task passed to the agent.\n"
            "- For any task related to scheduled taks, use 'scheduler_agent'.\n"
            "-- Do not call any other assistant when asking for scheduled tasks. Just use 'scheduler_agent' on 'call_agent' tool.\n"
            "- For any transaction related (getting user's positions included) to Drift Vaults (the token is always USDC if not specified), use 'drift_vaults_agent'.\n"
            "- For any transaction/question related to Drift PERPS (like how to use it, opening/closing a position, creating an account, depositing/withdrawing collateral, or any information required), use 'drift_perps_agent'.\n"
            " -- Do not ask for user wallet address, it's not necessary as the assistant is able to manage that.\n"
            "- For liquidity management, use 'lp_specialist_agent'.\n"
            "- For Solana deposits (not liquidity pools), use 'solana_yield_agent'.\n"
            "- For token transfers on EVM and Solana, use 'transfer_assistant'.\n"
            "- Once the task is completed, return the result following the JSON format. No summaries."
            "- Error handling: if any error occurs, or an assistant returns an error, explain very briefly to the user, ask him to try again changing the parameters or what he requested (if needed), or to try again later. Asking for more details is not an error.\n"
        ),
        tools=[FunctionTool(call_agent, description=f"Call the specialist agent to tackle the task with the current chat id {chat_id}.", strict=True)],
        reflect_on_tool_use=True,
    )

    updated_task = f"""Current Task: {task}. Current chat id is {chat_id}"""
    task_result = await automated_executor.run(task=updated_task, cancellation_token=CancellationToken())
    json_response = safe_parse(task_result.messages[-1].content)

    transaction = json_response.get("transaction", {})
    transaction_list = transaction.get("transactions", [])
    if len(transaction_list) > 0:
        for transaction_item in transaction_list:
            if transaction_item.get("serializedTransaction", ""):
                # call signWithDelegatedAction for solana
                await perform_automated_transaction(
                    transaction_id=transaction.get("transactionId", ""),
                    chat_id=chat_id,
                    user_id=user_id,
                    transaction_data=transaction_item.get("serializedTransaction", ""),
                    type="SOLANA",
                    action="signTransaction",
                    sender_wallet_address=sol_wallet_address,
                )
            else:
                # call signWithDelegatedAction for evm
                await perform_automated_transaction(
                    transaction_id=transaction.get("transactionId", ""),
                    chat_id=chat_id,
                    user_id=user_id,
                    transaction_data=transaction_item,
                    type="EVM",
                    action="signTransaction",
                    chain=str(transaction.get("fromChainId", "")),
                    sender_wallet_address=evm_wallet_address,
                )
    return

