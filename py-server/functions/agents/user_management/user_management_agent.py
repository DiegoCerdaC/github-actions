from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import Response
from autogen_core import CancellationToken
from typing import Annotated
from executor import process_chat_messages
from services.llm import gpt_4o_client
from autogen_agentchat.messages import TextMessage

from utils.firebase import (
    set_context_id,
    set_request_ctx,
    update_message,
    create_message_doc_id,
)
from services.voice import encode_audio_to_base64, generate_speech_from_text

import services.analytics as analytics
from services.tracing import tracer, set_status_ok, set_status_error, set_attributes

from agents.user_management.user_management_functions import (
    update_user,
    add_onboarding_ui_message,
)
from utils.firebase import set_request_ctx


@tracer.start_as_current_span("user_management_agent")
async def call_user_management_agent(
    task: Annotated[str, "The task to be completed by the user management agent."],
    user_id: Annotated[str, "The user's ID"],
    chat_id: Annotated[str, "The chat ID"],
    use_voice: bool = False,
) -> Annotated[str, "The chat history of the user management agent."]:
    """
    User Management Agent handles user onboarding and profile updates.
    """

    analytics.increment_agent_used("user_management_agent", chat_id)
    set_attributes(
        {
            "chat_id": chat_id,
            "task": task,
            "use_voice": use_voice,
            "user_id": user_id,
        }
    )

    set_context_id(chat_id)
    set_request_ctx(chat_id, "user_id", user_id)

    messages = process_chat_messages(chat_id)
    history_messages = messages.get("chat_history", [])
    current_response = messages.get("current_task", [])

    user_management_agent = AssistantAgent(
        name="User_Management",
        system_message=(
            "You are a helpful assistant that guides users through onboarding and helps them manage their profile settings.\n"
            "The onboarding process is as follows:\n"
            "1. Ask for their name once and wait for the user to respond.\n"
            f"2. Once the user name is known and 'risk_level' is either missing/None or invalid, ALWAYS call the 'add_onboarding_ui_message' tool with the component 'risk_profile' and the chat_id={chat_id} and user_id={user_id}.\n"
            "- A UI component will be rendered in the client to the user.\n"
            "- After calling the tool, ALWAYS ask the user to select the risk profile that best describes them.\n"
            "- Do not add any other sentence, question, or greeting in that message.\n"
            "- Only call this tool once.\n"
            "\n"
            "3. When you have the user name, and the risk profile the user wants to set, call 'update_user' tool with the following parameters:\n"
            f"user_id={user_id} - updates = dict with name:<user's name> - risk_profile:<risk profile> - onboarding_completed: ONBOARDED\n"
            "- After calling the tool, respond confirming that the account has been set up and the user can start using the app.\n"
            "- Do NOT send this message more than once.\n"
        ),
        model_client=gpt_4o_client,
        reflect_on_tool_use=True,
        tools=[update_user, add_onboarding_ui_message],
    )

    task = f"""
    Complete the onboarding flow for this user.
    Previous messages: {history_messages}
    Current user response: {current_response}.
    """

    try:
        message_id = create_message_doc_id(chat_id=chat_id)

        async for message in user_management_agent.on_messages_stream(
            messages=[TextMessage(content=task, source="user")],
            cancellation_token=CancellationToken(),
        ):
            # if message is a type of message chunk, write to message doc
            if isinstance(message, Response):
                content = message.chat_message.content
                await update_message(
                    chat_id=chat_id,
                    user_id=user_id,
                    message_id=message_id,
                    data={
                        "content": content,
                        "sender": "AI",
                        "voiceContent": "",
                        "useVoice": False,
                        "messageType": "text",
                    },
                )
            # then we get final response, which has all the message chunks concatenated together
            # use that to create the voice message
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

        set_status_ok()
        return
    except Exception as e:
        set_status_error(e)
        return f"An error occurred: {str(e)}"
