from autogen_agentchat.agents import AssistantAgent
from config import OPENAI_API_KEY
from autogen_ext.models.openai import OpenAIChatCompletionClient
from pydantic import BaseModel
import json
from agents.drift.drift_functions import select_vault_to_deposit_to
import services.analytics as analytics
from utils.firebase import save_ui_message, set_context_id
from autogen_core import CancellationToken
from autogen_core.tools import FunctionTool
from autogen_agentchat.messages import TextMessage
import ast


class DriftVault(BaseModel):
    vaultAddress: str
    vaultName: str
    vaultAge: int
    vaultTvl: float
    vaultPnl: float
    vaultRedeemPeriod: str
    percentagePNL: float
    reason: str


class AgentResponse(BaseModel):
    drift_vault: DriftVault


def safe_parse(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(text)
        except Exception as e:
            raise ValueError(f"Couln't parse the content. Error: {e}")


async def call_autonomous_drift_agent(chat_id: str):
    """
    This agent is responsible for proposing the user the best option within Drift Vaults.
    """
    analytics.increment_agent_used("autonomous_lulo_drift_agent", chat_id)

    set_context_id(chat_id)

    get_drift_vaults = FunctionTool(
        select_vault_to_deposit_to,
        description="Get available drift vaults to analyze them and select the best one.",
        strict=True,
    )

    llm_with_structured_output = OpenAIChatCompletionClient(
        model="gpt-4o",
        api_key=OPENAI_API_KEY,
        response_format=AgentResponse,
    )

    drift_vaults_analyzer = AssistantAgent(
        name="drift_vaults_analyzer",
        system_message=(
            "You're a blockchain assistant using Drift to analyze vaults and suggest the best one to the user.\n"
            "Call `select_vault_to_deposit_to` to find availables vaults options to deposit to (using ALWAYS the frontend_quotiong on FALSE).\n"
            "The tool will provide a list of drift vaults. You have to analyze them and select the best one.\n"
            "When you have concluded, you must give your selection and yours reasonings following the JSON format and then reply TERMINATE. "
        ),
        model_client=llm_with_structured_output,
        tools=[get_drift_vaults],
    )

    detailed_task = """
        Your task is to ensure that the user's USDC is always deposit in the best vault.
        Identify the best drift vault by calling `select_vault_to_deposit_to` and analyzing the information retrieved.

        **Important Considerations:**     
        - If a function call returns an error, return the error message and end the conversation.
        - ONLY CALL ONE FUNCTION AT A TIME AND WAIT UNTIL THE FUNCTION IS COMPLETED TO CALL THE NEXT ONE.
        - ALWAYS reply in the structured format, do not reply anything else. Example: 
            {
                "drift_vault": {
                    "vaultAddress": "...",
                    "vaultName": "...",
                    "vaultAge": ...,
                    "vaultTvl": ...,
                    "vaultPnl": ...,
                    "vaultRedeemPeriod": ...,
                    "percentagePNL": ...,
                    "reason": "..."
                }
            }
        *** EXECUTE ALL THE FUNCTIONS BEFORE FINISHING OR TERMINATING THE CONVERSATION***
    """
    try:
        chat_result = await drift_vaults_analyzer.on_messages(
            messages=[
                TextMessage(
                    content=detailed_task,
                    source="user",
                )
            ],
            cancellation_token=CancellationToken(),
        )

        result_message = chat_result.chat_message.content
        json_response = safe_parse(result_message)

        json_response = sorted(
            json_response, key=lambda x: x["percentagePNL"], reverse=True
        )

        best_option = {"drift_vault": json_response[0]}

        save_ui_message(
            chat_id="risky-chat",
            component="automated_suggestions",
            renderData={**best_option},
        )
        return json_response
    except Exception as e:
        return f"An error occurred: {str(e)}"
