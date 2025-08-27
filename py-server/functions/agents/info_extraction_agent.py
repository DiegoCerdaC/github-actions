from typing import List, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from pydantic import BaseModel
from enum import Enum
import json
from config import OPENAI_API_KEY
from autogen_ext.models.openai import OpenAIChatCompletionClient


class InformationType(str, Enum):
    USER_PREFERENCE = "user_preference"
    INTERACTION = "interaction"


class ExtractedItem(BaseModel):
    content: str
    type: InformationType


class ExtractedInformation(BaseModel):
    items: List[ExtractedItem]
    reasoning: Optional[str] = None

    class Config:
        extra = "forbid"


llm_with_structured_output = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=OPENAI_API_KEY,
    response_format=ExtractedInformation,
)


async def extract_information_agent(text: str) -> ExtractedInformation:
    """
    Extracts structured information from text using the LLM agent.
    Args:
        text (str): The text to extract information from
    Returns:
        ExtractedInformation: Structured information extracted from the text
    """
    info_extractor = AssistantAgent(
        name="info_extractor",
        model_client=llm_with_structured_output,
        system_message=(
            "You are an expert at extracting structured information from user messages for a blockchain application. "
            "Your task is to identify and categorize information from the user's input into two types:\n\n"
            "1. USER_PREFERENCE: User's preferences, habits, or stated behaviors about blockchain/crypto operations.\n"
            "   Examples:\n"
            "   - 'I only swap on Solana'\n"
            "   - 'I prefer staking mSOL'\n"
            "   - 'I like trading meme coins'\n"
            "   - 'I'm a conservative trader'\n\n"
            "2. INTERACTION: Specific actions, queries, or operations the user is performing or asking about.\n"
            "   Examples:\n"
            "   - 'Swap 1 USDC for SOL'\n"
            "   - 'How is the market today?'\n"
            "   - 'Bridge 100 USDC to Base'\n"
            "   - 'What's the price of BTC?'\n\n"
            "IMPORTANT RULES:\n"
            "1. Each piece of information should be categorized as either a USER_PREFERENCE or INTERACTION.\n"
            "2. For USER_PREFERENCE, focus on statements that indicate user habits, preferences, or general behaviors.\n"
            "3. For INTERACTION, focus on specific actions, queries, or operations.\n"
            "4. If a message contains both types, extract them separately.\n"
            "5. If no relevant information is found, return an empty items array.\n"
            "6. Keep the content as close to the original text as possible while maintaining clarity.\n\n"
            "Respond with a structured JSON object containing:\n"
            "- items: array of objects with 'content' and 'type' fields\n"
            "- reasoning: optional explanation for ambiguous cases"
        ),
    )

    prompt = f"""
    Extract structured information from the following message:
    
    {text}
    
    Categorize the information into either USER_PREFERENCE or INTERACTION.
    USER_PREFERENCE should capture user habits, preferences, or general behaviors.
    INTERACTION should capture specific actions, queries, or operations.
    
    If the message contains multiple pieces of information, extract them separately.
    Keep the content as close to the original text as possible.
    
    Respond with a structured JSON object containing:
    - items: array of objects with 'content' and 'type' fields
    - reasoning: optional explanation for ambiguous cases
    """

    try:
        chat_result = await info_extractor.on_messages(
            messages=[TextMessage(content=prompt, source="user")],
            cancellation_token=CancellationToken(),
        )

        result_message = chat_result.chat_message.content
        response_dict = json.loads(result_message)

        # Ensure items array is present, even if empty
        default_response = {
            "items": [],
            "reasoning": response_dict.get("reasoning", None),
        }

        default_response.update(response_dict)
        return ExtractedInformation(**default_response)

    except Exception as e:
        return ExtractedInformation(
            items=[],
            reasoning=f"Extraction failed due to error: {str(e)}",
        )
