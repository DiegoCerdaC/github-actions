import os
from typing import Annotated, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
import services.analytics as analytics
from services.llm import gpt_4o_client
from agents.orbit_rag_agent.orbit_document_searcher import OrbitDocumentSearcher
from services.tracing import set_status_ok, set_status_error, tracer, set_attributes
from utils.firebase import save_ui_message
from services.tokens import tokens_service


# Tool function for showing a TokenCard UI
async def show_token_card_ui(
    chat_id: Annotated[str, "The current chat id"],
    token_symbol_or_address: Optional[str] = None,
    chain: Optional[str] = None,
):
    token_metadata = None
    if token_symbol_or_address and chain:
        token_metadata = tokens_service.get_token_metadata(
            chain=chain, token=token_symbol_or_address
        )
        if not token_metadata:
            return f"Token {token_symbol_or_address} on {chain} is not supported."
        thought = f"Showing info for {token_metadata['symbol']} on {chain}."
    else:
        thought = "Showing supported tokens and chains."

    save_ui_message(
        chat_id=chat_id,
        component="token_card",
        renderData={
            "token": token_metadata if token_metadata else None,
            "chain": chain,
            "type": "INFO",
        },
        thought=thought,
        isFinalThought=True,
    )
    if token_metadata:
        return f"Here is information about {token_symbol_or_address} on {chain}."
    else:
        return "Here are the supported tokens and chains."


@tracer.start_as_current_span("orbit_rag_agent")
async def call_orbit_rag_agent(
    task: str, chat_id: str, use_frontend_quoting: bool = True
) -> str:
    """
    A specialized agent for answering questions about Orbit using RAG (Retrieval-Augmented Generation).
    Uses Firestore for vector storage and retrieval of relevant information.


    Examples:
    - What is Orbit's vision?
    - Tell me about Orbit's tokenomics
    - What's in Orbit's roadmap for Q1 2024?
    - How does Orbit's token work?
    - What chains does Orbit support?
    - Which protocols are available on Orbit?
    - What tokens do you support?
    - Which tokens or chains can I use?
    - Show me info for USDC on Solana

    Args:
        task (str): Question about Orbit
        chat_id (str): The current chat id
        use_frontend_quoting (bool): Whether to use frontend quoting or not


    Returns:
        str: Answer to the question about Orbit
    """
    analytics.increment_agent_used("orbit_rag", chat_id)
    set_attributes(
        {"chat_id": chat_id, "task": task, "use_frontend_quoting": use_frontend_quoting}
    )

    try:
        # Initialize document searcher
        indexer = OrbitDocumentSearcher(collection_name="orbit_docs")


        # Search for relevant information
        retrieved_info = await indexer.search_similar(task, limit=10)
        if not retrieved_info:
            return "I'm sorry, I couldn't find relevant information to answer your question."


        # Create the assistant agent with context
        orbit_agent = AssistantAgent(
            name="Orbit_RAG_Assistant",
            system_message=(
                "You are Orbit. Please answer questions about Orbit, its features, and supported protocols. Please be clear and concise. "
                "If the user asks about a specific token or chain, or about supported tokens/chains, call the 'show_token_card_ui' tool just once with the token symbol or address and chain if provided."
                "Do not mention tool names or implementation details in your response. Never call the tool more than once."
            ),
            model_client=gpt_4o_client,
            tools=[show_token_card_ui],
        )

        updated_task = f"Task: '{task}'.\nChatId is {chat_id}"

        # Process the task
        chat_result = await orbit_agent.on_messages(
            messages=[
                TextMessage(
                    content=f"Retrieved information: {retrieved_info}", source="user"
                ),
                TextMessage(content=updated_task, source="user"),
            ],
            cancellation_token=CancellationToken(),
        )

        set_status_ok()
        return chat_result.chat_message.content


    except Exception as e:
        set_status_error()
        raise e

