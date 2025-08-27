from agents.researcher_agent.tools import (
    create_twitter_agent,
    create_education_agent,
    create_portfolio_agent,
    create_defi_llama_agent,
    create_dexscreener_agent,
    create_coinmarketcap_agent,
    create_market_analysis_agent,
    create_meme_trader_agent,
)
import services.analytics as analytics
from services.llm import gpt_4o_client
from services.tracing import set_status_ok, set_status_error, tracer, set_attributes
from utils.single_agent_team import SingleAgentTeam


@tracer.start_as_current_span("researcher_agent")
async def call_researcher_agent(
    task: str, chat_id: str, use_frontend_quoting: bool = True
) -> str:
    """
    Conducts crypto research, education and social analysis using:
    - CoinMarketCap: Price data and market trends
    - DexScreener: New and boosted DEX tokens
    - Twitter: Tweet analysis and account monitoring
    - Web Search: Additional context gathering
    - DeFiLlama: Top protocols, chains, DEXs and yields pools
    - MemeTrader: Meme token analysis and trading recommendations
    Examples:
    - "Get latest tweets from @xxx"
    - "How did PEPE perform last 7 days"
    - "Show newest Dexscreener tokens"
    - "Top crypto gainers 24h"
    - "Analyze @xxx tweets for token mentions"
    - "Show market summary"
    - "What are the top chains by TVL?"
    - "Give me the top 3 protocols on Polygon"
    - "Show me the top DEXs on Solana"
    - "What are the top yields pools on Ethereum"
    - "What are the top meme tokens on Solana"
    - "Give me meme tokens recommendations"
    Args:
       task (str): Query for crypto research, education or social monitoring
       chat_id (str): The current chat id
       use_frontend_quoting (bool): Whether to use frontend quoting or not. Default is True.
    Returns:
       str: Research findings or error message
    """

    analytics.increment_agent_used("researcher", chat_id)
    set_attributes(
        {"chat_id": chat_id, "task": task, "use_frontend_quoting": use_frontend_quoting}
    )

    try:
        # create agent tools
        twitter_assistant = create_twitter_agent(
            chat_id=chat_id, task=task, use_frontend_quoting=use_frontend_quoting
        )
        education_assistant = create_education_agent(
            chat_id=chat_id, use_frontend_quoting=use_frontend_quoting
        )
        portfolio_assistant = create_portfolio_agent(
            chat_id=chat_id, use_frontend_quoting=use_frontend_quoting
        )
        defi_llama_assistant = create_defi_llama_agent(
            chat_id=chat_id, use_frontend_quoting=use_frontend_quoting
        )
        dexscreener_assistant = create_dexscreener_agent(
            chat_id=chat_id, use_frontend_quoting=use_frontend_quoting
        )
        coinmarketcap_assistant = create_coinmarketcap_agent(
            chat_id=chat_id, use_frontend_quoting=use_frontend_quoting
        )
        market_analysis_assistant = create_market_analysis_agent(
            chat_id=chat_id, use_frontend_quoting=use_frontend_quoting
        )
        meme_trader_assistant = create_meme_trader_agent(
            chat_id=chat_id, use_frontend_quoting=use_frontend_quoting
        )

        # create round-robin-group-chat with single agent
        researcher_agent = SingleAgentTeam(
            name="Research_Assistant",
            system_message=(
                f"You are a comprehensive cryptocurrency researcher. Current chat id is: {chat_id}. "
                f"And use_frontend_quoting is ALWAYS {use_frontend_quoting}. "
                "Here's what you can do:\n"
                "1. For general questions regarding blockchain, use 'education_assistant'.\n"
                "2. For anything related to twitter, use 'twitter_assistant'.\n"
                "3. For user wallet and portfolio, use 'portfolio_assistant'.\n"
                "4. For questions about blockchain protocols, chains dexes, and yield pools, use 'defi_llama_assistant'.\n"
                "5. For anything related to boosted tokens, newest tokens and token pair lookups, use 'dexscreener_assistant'.\n"
                "6. For finding out trending tokens, token prices, highest crypto gainers, use 'coinmarketcap_assistant'.\n"
                "7. For market analysis, use 'market_analysis_assistant'.\n"
                "8. Combined Research:\n"
                "For Deep Analysis:\n"
                "- Check price data\n"
                "- Look at social media activity\n"
                "- Search latest news\n"
                "- Monitor official project accounts\n"
                "- Track founder/dev updates\n"
                "- Analyze portfolio performance\n"
                "For Trending Topics:\n"
                "- Cross-check social media buzz\n"
                "- Look for recent news/announcements\n"
                "- Analyze market movements\n"
                "- Compare with portfolio performance\n"
                "Key Points:\n"
                "- Will explain any errors clearly\n"
                "Every response will end with: Brief summary of findings (prices, tweets, market data, etc)."
            ),
            model_client=gpt_4o_client,
            tools=[
                twitter_assistant,
                education_assistant,
                portfolio_assistant,
                defi_llama_assistant,
                dexscreener_assistant,
                coinmarketcap_assistant,
                market_analysis_assistant,
                meme_trader_assistant,
            ],
            reflect_on_tool_use=True,
        ).get_instance()

        chat_result = await researcher_agent.run(task=task)
        set_status_ok()
        # iterating over list in reverse order
        for i in range(len(chat_result.messages) - 1, -1, -1):
            content = chat_result.messages[i].content
            if content != "TERMINATE":
                return content.replace("TERMINATE", "")
        return "I've completed my task."
    except Exception as e:
        set_status_error(e)
        print(f"Error in researcher agent: {str(e)}")
        raise
