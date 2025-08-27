from autogen_agentchat.agents import AssistantAgent
from services.voice import encode_audio_to_base64, generate_speech_from_text
from autogen_agentchat.base import Response
from autogen_agentchat.messages import TextMessage, ModelClientStreamingChunkEvent
from autogen_core import CancellationToken
from utils.firebase import (
    update_message,
    create_message_doc_id,
)
from services.llm import gpt_4o_client


async def generate_error_message(
    chat_id, user_id, chat_summary, frontend_error, use_voice=False
):
    """
    Receives an error from the frontend and generates a response to the user in a "human way".

    Args:
        chat_id (str): The ID of the chat to summarize
        frontend_error (str): The error message from the frontend

    Returns:
        str: The generated error message
    """
    error_agent = AssistantAgent(
        name="error_agent",
        model_client=gpt_4o_client,
        system_message=(
            "You are a professional assistant who helps users understand technical issues in a clear and empathetic manner. "
            "Explain errors in straightforward language, focusing on what the user might be experiencing. "
            "Avoid technical jargon and do not mention system failures, or error 500, or similar known development errors or axios errors."
            "Just explain the error in a way that is easy to understand, offering simple suggestions or asking if they'd like more help."
        ),
        reflect_on_tool_use=False,
        model_client_stream=True,
    )

    prompt = f"""The user chat summary is: {chat_summary}        
        There was an error on his latest intent: {frontend_error}
        Please explain the following error message in a clear and simple way, avoiding technical terms: """
    try:
        message_id = create_message_doc_id(chat_id=chat_id)
        async for message in error_agent.on_messages_stream(
            messages=[TextMessage(content=prompt, source="user")],
            cancellation_token=CancellationToken(),
        ):
            if isinstance(message, ModelClientStreamingChunkEvent):
                await update_message(
                    chat_id=chat_id,
                    user_id=user_id,
                    message_id=message_id,
                    data={
                        "content": message.content,
                        "sender": "AI",
                        "voiceContent": "",
                        "useVoice": False,
                        "messageType": "text",
                    },
                )

            elif isinstance(message, Response) and use_voice:
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
    except Exception as e:
        print(f"Error generating error message: {e}")

    return
