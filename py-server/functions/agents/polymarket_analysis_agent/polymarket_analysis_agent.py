from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from typing import Annotated, TypedDict, Optional
from services.llm import gpt_4o_client
from utils.firebase import save_polymarket_event_to_rumours_collection


class PolymarketEvent(TypedDict):
    id: str
    title: str
    description: Optional[str]


async def call_polymarket_analysis_agent(
    event_data: PolymarketEvent,
) -> Annotated[str, "The result of analyzing Polymarket events."]:
    """
    Analyzes a single Polymarket event to determine if it should be moved to the rumours collection.

    This agent evaluates a Polymarket event based on:
    1. Whether it could impact crypto markets (BTC, ETH, SOL)
    2. Whether the event format is actionable (not ambiguous)
    3. Whether date-based events should be converted to tweet-based events

    Args:
        event_data (PolymarketEvent): The Polymarket event to analyze

    Returns:
        str: Response from the agent indicating the success or failure of processing
    """

    analysis_agent = AssistantAgent(
        name="polymarket_analysis_agent",
        system_message=(
            "You are an expert AI agent specialized in analyzing Polymarket events to determine their relevance for crypto trading. "
            "Your primary function is to evaluate whether events could impact Bitcoin (BTC), Ethereum (ETH), or Solana (SOL) prices. "
            "\n\n"
            "ANALYSIS CRITERIA: "
            "1. MARKET IMPACT: Does this event have the potential to move crypto markets? "
            "   - Direct crypto events (e.g., 'Vitalik Buterin goes to jail' -> DOWN, 'Tether collapses' -> DOWN, 'Crypto adoption increases' -> UP) "
            "   - Geopolitical events (e.g., 'Palestine launches major attack on Israel' -> DOWN) "
            "   - Economic events (e.g., 'US inflation data above expectations' -> DOWN, 'Fed rate cut' -> UP) "
            "   - Regulatory events (e.g., 'SEC bans all cryptocurrencies' -> DOWN, 'China reverses crypto ban' -> UP) "
            "   - Major tech events (e.g., 'Elon Musk announces X accepts Bitcoin' -> UP) "
            "   - Exchange/Infrastructure events (e.g., 'Major crypto exchange hack' -> DOWN) "
            "\n\n"
            "2. ACTIONABILITY: Is the event format actionable for trading? "
            "   - GOOD: Specific events with clear market direction "
            "     * 'Vitalik Buterin goes to jail' -> DOWN (clear bearish signal) "
            "     * 'Tether (USDT) collapses' -> DOWN (clear bearish signal) "
            "     * 'Major crypto exchange hack' -> DOWN (clear bearish signal) "
            "     * 'China reverses crypto ban' -> UP (clear bullish signal) "
            "   - BAD: Ambiguous or vague events "
            "     * 'Will ETH be greater than $3900 on August 1?' (ambiguous direction) "
            "     * 'Will there be a crypto hack?' (too vague, no specific target) "
            "     * 'Will crypto prices be volatile?' (too vague) "
            "     * 'Will markets be affected?' (too vague) "
            "\n\n"
            "3. EVENT TYPE CONVERSION: "
            "   - Date-based events should be converted to tweet-based events "
            "   - Example: 'Israel strikes Yemen by August 15?' -> Convert to tweet-based and fix title to 'Israel strikes Yemen?'"
            "   - This allows for immediate execution when news breaks "
            "   - Set tweetBased = True for geopolitical/economic events that can happen anytime "
            "\n\n"
            "MARKET DIRECTION ANALYSIS: "
            "BULLISH EVENTS (expect markets to go UP): "
            "- 'Crypto adoption increases' (increases confidence in crypto) "
            "- 'Binance Market Cap surpasses Nike Market Cap' (increases confidence in crypto) "
            "- 'China reverses crypto ban' (regulatory approval) "
            "- 'Elon Musk announces X accepts Bitcoin' (adoption) "
            "- 'Fed Interest Rate Decision below expectations' (lower rates = bullish) "
            "- 'SEC approves spot Bitcoin ETF' (regulatory approval) "
            "\n\n"
            "BEARISH EVENTS (expect markets to go DOWN): "
            "- 'Vitalik Buterin goes to jail' (decreases confidence in crypto) "
            "- 'Tether (USDT) collapses' (stablecoin failure = panic) "
            "- 'Ethereum Foundation disappear' (loss of confidence) "
            "- 'Major crypto exchange hack' (security concerns) "
            "- 'SEC bans all cryptocurrencies' (regulatory crackdown) "
            "- 'US inflation data above expectations' (higher rates = bearish) "
            "- 'Palestine launches major attack on Israel' (geopolitical risk) "
            "- 'Russia escalates war with nuclear threat' (geopolitical risk) "
            "- 'Higher than 20% tariff on India by US' (trade war risk) "
            "\n\n"
            "5. TITLE DATE CLEANUP POLICY: "
            "If the event title contains any date reference, you must remove it completely. "
            "This includes absolute dates (e.g., 'on July 8', 'August 15') and relative expressions (e.g., 'before next Friday', 'in 3 days'). "
            "Example: "
            "Original: 'US inflation rises above 5% on July 8' "
            "Updated: 'US inflation rises above 5%' "
            "Do not add or replace with other wording (e.g., do not say 'soon', 'eventually', etc.). Just delete the date. "
            "This modification applies only to the title, not the description. "
            "After removing the date, you must classify the event as: "
            "- is_tweet_based = True if it is an unscheduled event (e.g., hack, arrest, collapse). "
            "- is_tweet_based = False if it is a scheduled institutional event (e.g., central bank decisions, elections, court rulings). "
            "If in doubt, prefer setting is_tweet_based = True."
            "DECISION MATRIX: "
            "- RELEVANT + ACTIONABLE + CLEAR DIRECTION: [APPROVE] Move to rumours collection "
            "- RELEVANT + AMBIGUOUS DIRECTION: [REJECT] Skip (unclear trading signal) "
            "- NOT RELEVANT: [REJECT] Skip (no crypto market impact) "
            "\n\n"
            "FUNCTIONS: "
            "- Use 'save_polymarket_event_to_rumours_collection' for events that pass the analysis. "
            "  - If the event is tweet based, set is_tweet_based to True. "
            "  - If the event needs a new title or description, set new_title to the new title and new_description to the new description. "
            "- The save function will automatically check for duplicates "
            "\n\n"
            "IMPORTANT: Your decisions directly affect automated trading opportunities. "
            "Be thorough in analysis and err on the side of including relevant events. "
            "Focus on events that can provide clear trading signals for BTC, ETH, or SOL. "
            "The key is identifying events with CLEAR market direction (UP or DOWN). "
        ),
        model_client=gpt_4o_client,
        reflect_on_tool_use=True,
        tools=[save_polymarket_event_to_rumours_collection],
    )

    try:
        # Create analysis task for the single event
        analysis_task = f"""
        Analyze the following Polymarket event to determine if it should be moved to the rumours collection:
        
        Event: {event_data}
        
        Evaluate:
        1. Does it have potential to impact BTC, ETH, or SOL prices?
        2. Is the event format actionable (not ambiguous)?
        3. Should date-based events be converted to tweet-based events?
        4. What is the expected market direction (UP or DOWN)?
        
        For relevant and actionable events:
        - Call 'save_polymarket_event_to_rumours_collection' with the event data
        - If it's a date-based event, set tweetBased to True
        - Update the title/description if needed for clarity
        
        Provide your analysis and decision for this event.
        """

        result = await analysis_agent.on_messages(
            messages=[TextMessage(content=analysis_task, source="user")],
            cancellation_token=CancellationToken(),
        )

        # Ensure the response content is properly encoded
        try:
            return result.chat_message.content
        except UnicodeEncodeError:
            # If there are encoding issues, return a sanitized version
            return result.chat_message.content.encode("ascii", "ignore").decode("ascii")

    except Exception as e:
        # Try to handle encoding errors specifically
        if "charmap" in str(e) or "UnicodeEncodeError" in str(e):
            return f"An encoding error occurred during analysis. Event processed but response contained unsupported characters."
        return f"An error occurred during analysis: {str(e)}"
