import services.analytics as analytics
from services.llm import gpt_4o_client
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import Swarm
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from agents.researcher_agent.functions import (
    get_tweets_from_key_accounts,
    get_multiple_tokens_pair_info,
)
from agents.automated_memecoin_trader.memecoin_functions import (
    get_top_holdings_of_traders,
)
from utils.firebase import db_save_message, set_context_id


async def call_automated_memecoin_trader_agent(chat_id: str):
    """
    The Automated Memecoin Trader analyzes information from Twitter, Dexscreener, known trader wallets, and other sources to suggest which token a user should buy. It works on SOLANA.
    """
    analytics.increment_agent_used("automated_memecoin_trader", chat_id)

    set_context_id(chat_id)

    planner = AssistantAgent(
        model_client=gpt_4o_client,
        name="planner",
        handoffs=[
            "twitter_assistant",
            "dexscreener_assistant",
            "holding_analyzer_assistant",
            "trading_and_swap_assistant",
        ],
        system_message="""You are a trading strategy coordinator for the Automated Memecoin Trader.
        Your role is to coordinate the strategy by delegating tasks to specialized assistants in a sequential workflow.

        Agents and their roles:
        - Twitter Assistant: Analyzes social media trends and sentiment for memecoins.
        - Dexscreener Assistant: Provides market insights on token pairs, including price, volume, and transaction trends.
        # - Holding Analyzer Assistant: Analyzes the top holdings of known crypto traders to identify popular tokens.
        - Trading And Swap Assistant: Consolidates all gathered data, selects the best token to swap to, and builds the swap quote for the recommended token.

        Workflow:
        1. **Data Collection**: 
        - Start by calling the agents one at a time in the following order: Twitter Assistant → Dexscreener Assistant -> Holding Analyzer Assistant
        - Wait until each agent finishes before proceeding to the next one.
        - Collect the information from each assistant before proceeding to the next one.
        2. **Analyzing Info And Swap Execution**: 
        - Once you have a token recommendation, call the Trading And Swap Assistant to decide the best token to swap into or out from.
        4. **Completion**:
        - Use "TERMINATE" once the Trading and Swap Builder Assistant has finished.

        Error Handling:
        - If any function throws an error, return the error message immediately and notify the user.
        - If any assistant fails to provide the necessary information, ask for clarification or notify the user.
        - If no final decision can be made because of errors or inadequate information to make a judgement from the Trading Expert or Swap Builder Assistant, state the reason to user and reply TERMINATE.
        Your goal is to ensure the entire trading strategy is executed smoothly and accurately based on the information from all assistants.""",
    )

    twitter_agent = AssistantAgent(
        name="twitter_assistant",
        model_client=gpt_4o_client,
        handoffs=["planner"],
        tools=[get_tweets_from_key_accounts],
        system_message="""You are a social sentiment analyst specializing in memecoin trading.
        Use the get_tweets_from_key_accounts tool to gather and analyze the most recent tweets from top crypto users.
        - Focus on identifying trends, sentiment, and potential signals for memecoin price movements.
        - Raise an exception if API rate limits are reached or if an error occurs, and notify the planner.
        - Always summarize key insights clearly before handing off to the planner for strategy integration.
        - You are NOT responsible for building any swap quote. Just provide information.
        Always handoff back to planner once you get all the information""",
    )

    dexscreener_agent = AssistantAgent(
        name="dexscreener_assistant",
        model_client=gpt_4o_client,
        handoffs=["planner"],
        tools=[get_multiple_tokens_pair_info],
        system_message="""You are a crypto market data analyst specializing in token pair analysis for memecoin trading.
    Use the get_multiple_tokens_pair_info tool to fetch and analyze token pair information from Dexscreener for multiple tokens. Always use the render_ui parameter as False. And the token_symbols should be the token symbols you want to get the information for (List).
    - Focus on retrieving market insights such as price, volume, market cap, transaction trends (buys/sells), and 24-hour price changes for token pairs.
    - Ensure the analysis highlights actionable trading signals, such as unusual trading volumes or price trends.
    - If any token pair data is unavailable or an error occurs, notify the planner immediately and explain the issue.
    
    Additional Context:
    - Always validate the data before providing insights.
    - Summarize the key findings, such as market performance and potential opportunities, before handing off to the planner.
    - Maintain clarity and conciseness in your analysis.
    - You are NOT responsible for building any swap quote. Just provide information.
    Always handoff back to planner once you get all the information""",
    )

    holding_analyzer_agent = AssistantAgent(
        name="holding_analyzer_assistant",
        model_client=gpt_4o_client,
        handoffs=["planner"],
        tools=[get_top_holdings_of_traders],
        system_message="""You are a holding analysis expert specializing in memecoin trading.
    Your task is to analyze the top holdings of known crypto traders to identify popular tokens they are currently holding.

    Workflow:
    - Use the get_top_holdings_of_traders tool to retrieve wallet balances and identify top-held tokens.
    - Cross-check these tokens (using the symbol or address) to determine if they match the memecoins being evaluated.
    - Highlight any memecoins that top traders are actively holding as potential buy signals.

    Instructions:
    - Notify the planner if any trader data is missing or if an error occurs.
    - Always summarize the top holdings and key findings before handing off to the planner.
    - Ensure all analysis is clear, actionable, and aligned with the overall trading strategy.
    Always handoff back to planner once you the holdings of the wallets""",
    )

    # Right now, there's no interactive view and we have no way of getting user's wallet address,
    # so we're just going to have agent report their analysis and user can manually offer the swap or not.
    trading_and_swap_agent = AssistantAgent(
        name="trading_and_swap_assistant",
        model_client=gpt_4o_client,
        handoffs=["planner"],
        system_message="""You are an assistant specializing in memecoin trading on the Solana blockchain.
        Your role is to analyze all the information provided by the other assistants and select the most promising tokens and determine whether to buy, hold, or sell them.

        Workflow:
        1. Analyze the information provided by the other assistants.
        2. Determine if there's any:
        - promising memecoin tokens to buy.
        - promising memecoin tokens that can be potentially hold.
        - memecoin tokens that can be sold.
        If there's none to buy or sell, be explicit about your reasonings.
        3. Be sure to analyze all information provided and make the best choices.

        Instructions:
        - If any data is missing or an error occurs during the process, notify the planner immediately.
        - Always handoff back to planner once you have the finished calling the functions to build the swap quote.
        """,
    )

    updated_task = f"""
        Chat id is {chat_id}
        Your goal is to research, consolidate the analysis, and recommend the top memecoin to buy or which to sell based on:
        - Twitter sentiment and trends.
        - Market data like price, volume, and trends.
        - Top holdings of known crypto traders.

        Workflow:
        1. Gather and analyze social, market and traders holdings data. Only call one agent at a time.
        2. Ensure all insights are accurate and complete before forming a recommendation.
        3. If data is missing or errors occur, request clarification or notify the user.
        4. Ensure to pass (if you have it) the token address in your final recommendation.
        5. Ask what user wants to do with the recommended token(s) based on your final conclusions.
        6. Always return the token address in your final recommendation so the user can easily swap to it.
    """

    text_termination = TextMentionTermination("TERMINATE")
    max_messages_termination = MaxMessageTermination(max_messages=50)
    termination = text_termination | max_messages_termination

    try:
        memecoin_trading_team = Swarm(
            participants=[
                planner,
                twitter_agent,
                dexscreener_agent,
                holding_analyzer_agent,
                trading_and_swap_agent,
            ],
            termination_condition=termination,
        )
        chat_result = await memecoin_trading_team.run(task=updated_task)
        last_msg = chat_result.messages[-1]

        if last_msg.content == "TERMINATE":
            db_save_message(
                chat_id=chat_id,
                content=chat_result.messages[-2].content,
                sender="AI",
                user_id="",
                message_type="text",
                metadata={},
            )
            return chat_result.messages[-2].content
        else:
            db_save_message(
                chat_id=chat_id,
                content=last_msg.content,
                sender="AI",
                user_id="",
                message_type="text",
                metadata={},
            )
        return last_msg.content
    except Exception as e:
        return f"An error occurred: {str(e)}"
