from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from typing import Annotated

from services.llm import gpt_4o_client
import services.analytics as analytics
from services.tracing import set_status_ok, set_status_error, tracer, set_attributes
from agents.liquidation_agent.liquidation_functions import (
    liquidate_all_assets,
)


@tracer.start_as_current_span("liquidation_agent")
async def call_liquidation_agent(
    task: str, chat_id: str, use_frontend_quoting: bool = True
) -> Annotated[str, "The result of liquidating all assets."]:
    """
    Liquidation agent for liquidating all assets on SOLANA and EVM Chains
    Args:
        task (str): Liquidation description, can include the FIAT token to liquidate to. (USDC, USDT)
        chat_id (str): The current chat id
        use_frontend_quoting (bool): Whether to use frontend quoting or not
    Returns:
        str: Result or error description
    """
    try:
        analytics.increment_agent_used("liquidation", chat_id)
        set_attributes(
            {
                "chat_id": chat_id,
                "task": task,
                "use_frontend_quoting": use_frontend_quoting,
            }
        )

        liquidation_agent = AssistantAgent(
            name="liquidation_agent",
            system_message=(
                "You are a LIQUIDATION ASSISTANT that helps users liquidate their assets."
                "Your ONLY job is to call 'liquidate_all_assets' if users want to liquidate their assets when users say things like:\n"
                "- 'liquidate all my assets'\n"
                "- 'convert all my tokens'\n"
                "- 'liquidate everything'\n"
                "- 'consolidate my portfolio'\n"
                "Just call 'liquidate_all_assets' immediately.\n\n"
                f"use_frontend_quoting is ALWAYS {use_frontend_quoting}.\n"
                "Keep it simple - just call liquidate_all_assets for any liquidation request."
            ),
            model_client=gpt_4o_client,
            reflect_on_tool_use=False,
            tools=[
                liquidate_all_assets,
            ],
        )

        updated_task = (
            f"Task: '{task}'.\nChatId is {chat_id}"
        )

        chat_result = await liquidation_agent.on_messages(
            messages=[TextMessage(content=updated_task, source="user")],
            cancellation_token=CancellationToken(),
        )
        set_status_ok()
        return f"I've completed the task. Just created the liquidation transactions. Result: {chat_result.chat_message.content}"
    except Exception as e:
        set_status_error(e)
        return f"An error occurred inside liquidation_agent: {str(e)}"
