from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from utils.firebase import db, get_messages_by_chat, clean_message
from services.llm import gpt_4o_client
from firebase_admin import firestore


def update_chat_summary(chat_id, summary):
    """
    Update the chat document with the generated summary.
    
    Args:
        chat_id (str): The ID of the chat to update
        summary (str): The generated summary text
    """
    try:
        # Get the chat document reference
        chat_ref = db.collection("chats").document(chat_id)
        
        # Update the summary field
        chat_ref.set(
            {
                "summary": summary,
                "summaryUpdatedAt": firestore.SERVER_TIMESTAMP
            }, 
            merge=True
        )
        
        print(f"Successfully updated summary for chat {chat_id}")
    except Exception as e:
        print(f"Error updating chat summary: {e}")

async def generate_summary(chat_id, previous_summary=None):
    """
    Generate a summary of the chat conversation using AutoGen.
    
    Args:
        chat_id (str): The ID of the chat to summarize
        previous_summary (str, optional): The previous summary, if any
    
    Returns:
        str: The generated summary
    """
    # Create a summarizer agent using AutoGen
    summarizer_agent = AssistantAgent(
        name="summarizer_assistant",
        model_client=gpt_4o_client,
        system_message=(
            "You are a summarizer assistant that creates concise, informative summaries of conversations. "
            "Your summaries should capture the key points, requests, and outcomes of the conversation. "
            "Focus on what was accomplished, what was requested, and any important information exchanged. "
            "Keep summaries brief but comprehensive, highlighting the most important aspects of the conversation. "
            "If there are no new summaries to add, don't append any new summaries."
        ),
        reflect_on_tool_use=False
    )

    # Get the chat messages
    messages = get_messages_by_chat(chat_id)
    
    if not messages or len(messages) == 0:
        return previous_summary or "No messages in this conversation yet."
    
    # Format the messages for the summarizer
    formatted_messages = "\n\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in messages
    ])
    
    # Create the prompt for the summarizer
    prompt = "Please summarize the following conversation:\n\n" + formatted_messages
    
    # If there's a previous summary, include it
    if previous_summary:
        prompt += f"\n\nPrevious summary: {previous_summary}\n\nPlease update the summary based on the new messages."
    
    # Generate the summary using the AutoGen agent
    response = await summarizer_agent.on_messages(
        [TextMessage(content=prompt, source="user")],
        cancellation_token=CancellationToken()
    )
    summary = clean_message(response.chat_message.content)
    
    return summary

async def summarize_chat(chat_id):
    """
    Main function to summarize a chat and update the summary in Firebase.
    
    Args:
        chat_id (str): The ID of the chat to summarize
    """
    try:
        # Get the current chat document to check for existing summary
        chat_ref = db.collection("chats").document(chat_id)
        chat_doc = chat_ref.get()
        
        if not chat_doc.exists:
            print(f"Chat {chat_id} does not exist")
            return
        
        chat_data = chat_doc.to_dict()
        previous_summary = chat_data.get("summary", None)
        
        # Generate a new summary
        summary = await generate_summary(chat_id, previous_summary)
        
        # Update the chat document with the new summary
        update_chat_summary(chat_id, summary)
        
        return summary
    except Exception as e:
        print(f"Error in summarize_chat: {e}")
        return None
