from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from config import OPENAI_API_KEY
from autogen_ext.models.openai import OpenAIChatCompletionClient
from pydantic import BaseModel
import json
from services.llm import gpt_4o_client
from agents.dex_agent.stake_functions import get_pool_with_highest_apy
from agents.solana_yield_agent.lulo_yield_functions import (
    get_stable_coin_rates as fetch_best_yield_rates,
)
import services.analytics as analytics
from utils.firebase import save_ui_message, set_context_id

from services.tracing import set_status_ok, set_status_error, tracer, set_attributes


class StakingToken(BaseModel):
    name: str
    apy: float
    ticker: str
    reason: str


class YieldToken(BaseModel):
    name: str
    apr: float
    protocol: str
    address: str
    symbol: str
    logoURI: str
    token_minimum_amount: str
    reason: str


class AgentResponse(BaseModel):
    staking_token: StakingToken
    yield_token: YieldToken


async def call_conservative_agent(chat_id: str):
    """
    This agent is responsible for staking in the best possible option for the user.
    It checks for the best SOL staking option and performs unstaking from the current position (if existing),
    then stakes in the new option if it is not already in the best position.
    """
    analytics.increment_agent_used("conservative_agent", chat_id)

    set_context_id(chat_id)

    staking_analyzer = AssistantAgent(
        name="Staking_Analyzer",
        system_message=f"""
        Your role is to analyze the staking options for the user to ensure the user is always staked in the highest APY token.
        Call `get_pool_with_highest_apy` to find the liquid staking token with the highest APY.
        Return the liquid staking tokens with the highest APY.
        """,
        model_client=gpt_4o_client,
        tools=[get_pool_with_highest_apy],
    )

    yield_analyzer = AssistantAgent(
        name="Yield_Analyzer",
        system_message=f"""Your role is to find the best yield rates on solana for a user to ensure user is always on the highest APR.
        Call `fetch_best_yield_rates` to find the best yield rates for solana tokens.
        Return the list of yield rates with the best APR.
        """,
        model_client=gpt_4o_client,
        tools=[fetch_best_yield_rates],
    )

    llm_with_structured_output = OpenAIChatCompletionClient(
        model="gpt-4o",
        api_key=OPENAI_API_KEY,
        temperature=0.0,
        seed=None,
        response_format=AgentResponse,
    )

    main_analyzer = AssistantAgent(
        name="Main_Analyzer",
        system_message=(
            "Your role is to analyze the best liquid staking tokens with the highest APY and the list of best yield rates with the best APR. "
            "Analyze the information provided by the other analyzers and determine the best liquid staking token and "
            "the yield token with the highest APR for the current day returns. "
            "When you have concluded, you must give your selection and yours reasonings following the JSON format and then reply TERMINATE. "
        ),
        model_client=llm_with_structured_output,
    )

    # Right now, there's no interactive view and we have no way of getting user's wallet address,
    # so we're just going to have agent report their analysis and user can manually offer the swap or not.

    detailed_task = f"""
        Your task is to ensure that the user's SOL is always staked in the liquid staking token with the highest available APY.
        Identify the liquid staking token with the highest APY by calling `get_pool_with_highest_apy`.
        Idenfity the best yield rates with the highest APR by calling `find_and_render_better_rates`.
        Analyze the information provided and recommend the best liquid staking token and the best yield token.

        **Important Considerations:**     
        - If a function call returns an error, return the error message and end the conversation.
        - ONLY CALL ONE FUNCTION AT A TIME AND WAIT UNTIL THE FUNCTION IS COMPLETED TO CALL THE NEXT ONE.
        *** EXECUTE ALL THE FUNCTIONS BEFORE FINISHING OR TERMINATING THE CONVERSATION***
    """
    try:
        termination = MaxMessageTermination(max_messages=4) | TextMentionTermination(
            "TERMINATE"
        )
        team = RoundRobinGroupChat(
            [staking_analyzer, yield_analyzer, main_analyzer],
            termination_condition=termination,
        )
        chat_result = await team.run(task=detailed_task)
        last_msg = chat_result.messages[-1]
        if last_msg.content == "TERMINATE":
            last_msg = chat_result.messages[-2]

        json_response = json.loads(str(last_msg.content))

        save_ui_message(
            chat_id=chat_id,
            component="automated_suggestions",
            renderData={**json_response},
        )
        return last_msg.content
    except Exception as e:
        return f"An error occurred: {str(e)}"
