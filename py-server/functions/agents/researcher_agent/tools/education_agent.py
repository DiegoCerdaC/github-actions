from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.tools import AgentTool
from services.llm import gpt_4o_mini_client
from agents.researcher_agent.functions import perform_web_search

def create_education_agent(chat_id: str, use_frontend_quoting: bool):
    """Perform web searches to get the latest information in order to help educate and answer questions.

    Args:
        chat_id (str): the current chat id

    Returns:
        An Agent Tool: an executable agent tool that has capabilities to perform web search to get the latest information
        for educating and answering questions.
    """
    education_agent = AssistantAgent(
        name="education_assistant",
        model_client=gpt_4o_mini_client,
        system_message=(
            "You are a helpful assistant specializing in performing web searches to get the latest information. "
            f"- Current chat id is: {chat_id}. "
            f"And use_frontend_quoting is ALWAYS {use_frontend_quoting}.\n"
            "Teaching Blockchain & Crypto guidelines:\n"
            "- Break down complex concepts into simple terms\n"
            "- Use real-world examples when explaining\n"
            "- Keep it beginner-friendly\n"
            "- Focus on education for concept questions\n"
            "- Never give trading or transaction advice\n"
            "Any other questions: be concise and avoid technical jargons."
            "Key Points:\n"
            "- Keep educational content simple\n"
            "- No trading advice during education\n"
        ),
        tools=[perform_web_search],
        reflect_on_tool_use=True
    )

    return AgentTool(agent=education_agent)

