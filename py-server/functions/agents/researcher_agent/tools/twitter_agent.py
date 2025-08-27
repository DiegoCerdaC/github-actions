from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.tools import AgentTool
from services.llm import gpt_4o_mini_client
from utils.firebase import save_agent_thought
from agents.researcher_agent.functions import (
    load_twitter_accounts,
    search_user_by_usernames,
    get_recent_twitter_posts
)


def create_twitter_agent(chat_id: str, task: str, use_frontend_quoting: bool):
    """Get recent twitter posts/tweets and perform analyses.

    Args:
        chat_id (str): the current chat id
        task (str): the task to be executed
        use_frontend_quoting (bool): a boolean

    Returns:
        An Agent Tool: an executable agent tool that has capabilities to find recent twitter posts
    """
    account_info = []
    keywords = ["twitter", "tweet", "tweeter", "post"]
    if any(keyword in task.lower() for keyword in keywords):
        save_agent_thought(
            chat_id=chat_id,
            thought="Checking Twitter accounts...",
        )
        accounts = load_twitter_accounts()
        for account in accounts.get("accounts", []):
            if account["twitter_handle"].lower() in task.lower():
                account_info.append(account["twitter_handle"])

    twitter_agent = AssistantAgent(
        name="twitter_assistant",
        model_client=gpt_4o_mini_client,
        system_message=(
            "You are a helpful assistant specializing in retrieving recent posts/tweets and performing additional analysis on the retrieved tweets. "
            f"Current chat id is: {chat_id}. "
            f"And use_frontend_quoting is ALWAYS {use_frontend_quoting}.\n"
            f"No need to search for twitter usernames. Use these twitter accounts: {','.join(account_info)}\n" if len(account_info) > 0 else ""
            "Here's what you can do:\n"
            "1. Finding Twitter Users:\n"
            "- Can search multiple usernames at once\n"
            "- Handle lists with 'and' or ',' separators\n"
            "2. Getting Recent Tweets:\n"
            "- One user's tweets at a time\n"
            "- Ask for more info if username invalid\n"
            "Key Points:\n"
            "- Will notify on Twitter rate limits\n"
            "- Won't summarize direct tweet displays\n"
            "- Track specified Twitter accounts\n"
            "Account Monitoring:\n"
            "- Track specified Twitter accounts\n"
            "- Look for trading signals\n"
            "- Analyze mentioned tokens\n"
            "- Focus on account-specific insights\n"
            "- Combine data from multiple sources\n"
        ),
        tools=[search_user_by_usernames, get_recent_twitter_posts]
    )

    return AgentTool(agent=twitter_agent)


