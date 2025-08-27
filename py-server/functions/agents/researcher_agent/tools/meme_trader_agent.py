from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_core.tools import FunctionTool
from autogen_agentchat.tools import AgentTool
from autogen_ext.models.openai import OpenAIChatCompletionClient
from pydantic import BaseModel
import json

from agents.researcher_agent.functions.meme_trader_functions import get_top_3_memes
from services.balances import get_wallet_balance, BalanceServiceType
from utils.firebase import save_ui_message, get_request_ctx
from config import OPENAI_API_KEY
from services.tracing import set_status_ok, set_status_error
from utils.firebase import save_agent_thought


class TradingAction(BaseModel):
    swap_action: str
    swap_explanation: str
    from_token: str
    from_amount: float
    to_token_symbol: str
    to_token_address: str
    estimated_to_amount: float

    class Config:
        extra = "forbid"


class AgentResponse(BaseModel):
    trading_actions: list[TradingAction]


llm_with_structured_output = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=OPENAI_API_KEY,
    response_format=AgentResponse,
)

protocols_balance = ["lulo", "drift", "meteora"]


def get_best_balance_for_swap(user_balance):
    """
    Find the token balance with highest USD value
    """
    try:
        best_token = None
        max_usd_value = 0

        for token in [t for t in user_balance if t["chain"] == "SOLANA"]:
            is_protocol_balance = any(
                protocol.lower() in token["address"].lower()
                for protocol in protocols_balance
            )

            if token["usd_amount"] > max_usd_value and not is_protocol_balance:
                max_usd_value = token["usd_amount"]
                best_token = {
                    "address": token["address"],
                    "symbol": token["symbol"],
                    "amount": token["amount"],
                    "usd_value": token["usd_amount"],
                }

        return best_token
    except Exception as e:
        print("error getting best balance", e)
        return None


async def meme_trader_agent(chat_id: str, use_frontend_quoting: bool | None) -> str:
    """
    Analyzes top 3 meme tokens on Solana and suggests optimal trading swaps based on price history/indicators/user balance.
    Args:
        chat_id (str): the current chat id
        use_frontend_quoting (bool): a boolean
    Returns:
        str: Success result or error message
    """
    if use_frontend_quoting == None:
        use_frontend_quoting = True

    solana_wallet_address = get_request_ctx(chat_id, "solana_wallet_address")

    if not solana_wallet_address:
        set_status_error(
            "You must connect your Solana Wallet in order to use the Meme Trader Program"
        )
        return "You must connect your Solana Wallet in order to use the Meme Trader Program"

    save_agent_thought(
        chat_id=chat_id,
        thought="Fetching wallet balance...",
    )

    user_balance = get_wallet_balance(
        solana_wallet_address, BalanceServiceType.SOLANA.value
    )

    best_balance = get_best_balance_for_swap(user_balance)
    if not best_balance:
        set_status_error(
            "No available balance found for trading. Please fund your wallet with SOL"
        )
        return (
            "No available balance found for trading. Please fund your wallet with SOL"
        )

    save_agent_thought(
        chat_id=chat_id,
        thought=f"Found best balance: {best_balance['amount']} {best_balance['symbol']} (${best_balance['usd_value']})",
    )

    def fetch_top_memes():
        return get_top_3_memes(chat_id)

    get_top_3_memes_data = FunctionTool(
        fetch_top_memes,
        description="Get the top 3 trending meme tokens on Solana.",
        strict=True,
    )

    trader_assistant = AssistantAgent(
        name="Trader_Assistant",
        system_message=(
            "You are a cryptocurrency trading assistant focused on meme tokens on Solana.\n"
            "Your task is to provide expert analysis and recommendations for trading actions.\n"
            "You have access to the top 3 meme tokens, including their price history and technical indicators (RSI, SMA, EMA).\n"
            f"Current chat id is {chat_id}. Never mention the chat id to user.\n"
            "Ensure recommendations are based on these indicators and the user's best balance.\n"
            "Adhere to trading rules: invest no more than 25% of the balance in one token, maintain at least 15% in USDC, and avoid suggesting trades for tokens the user already owns.\n"
            "Provide clear reasoning for each recommendation, ensuring they are within the user's available balance."
        ),
        model_client=llm_with_structured_output,
        tools=[get_top_3_memes_data],
        reflect_on_tool_use=True,
    )

    try:
        save_agent_thought(
            chat_id=chat_id,
            thought="Analyzing trading opportunities...",
        )
        chat_result = await trader_assistant.on_messages(
            messages=[
                TextMessage(
                    content=f"Please suggest the most convenient swaps using my {best_balance['symbol']} balance ({best_balance['amount']} worth ${best_balance['usd_value']}) to trade with the top 3 Meme Tokens",
                    source="user",
                )
            ],
            cancellation_token=CancellationToken(),
        )

        result_message = chat_result.chat_message.content
        response_dict = json.loads(result_message)
        if response_dict["trading_actions"] == [] or all(
            "hold" in swap["swap_action"].lower()
            for swap in response_dict["trading_actions"][:3]
        ):
            set_status_ok()
            save_agent_thought(
                chat_id=chat_id,
                thought="No trading opportunities found. Recommending to hold current positions.",
                isFinalThought=True,
            )
            return (
                "No swaps suggested, the best option right now is to hold your balances"
            )
        if use_frontend_quoting:
            save_ui_message(
                chat_id=chat_id,
                renderData=response_dict,
                component="meme_trade_options",
                thought="Task completed successfully",
                isFinalThought=True,
            )
            set_status_ok()
            return "Meme trading suggestions successfully sent to the user"
        return response_dict
    except Exception as e:
        set_status_error(e)
        save_agent_thought(
            chat_id=chat_id,
            thought="Error occurred during trading analysis.",
            isFinalThought=True,
        )
        return f"An error occurred: {str(e)}"


def create_meme_trader_agent(
    chat_id: str, use_frontend_quoting: bool = True
) -> AgentTool:
    """
    Create a meme trader agent.
    Args:
        chat_id (str): the current chat id
        use_frontend_quoting (bool): a boolean
    Returns:
        An Agent Tool: an executable agent tool that has capabilities to analyze top 3 meme tokens on Solana and suggest optimal trading swaps based on price history/indicators/user balance.
    """
    return FunctionTool(
        meme_trader_agent,
        description=f"A meme trader agent that can analyze top 3 meme tokens on Solana and suggest optimal trading swaps based on price history/indicators/user balance. Use_frontend_quoting is ALWAYS {use_frontend_quoting} and current chat id is {chat_id}.",
        strict=True,
    )
