from typing import List, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TerminationCondition
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core.models import ChatCompletionClient


class SingleAgentTeam:
    """A class that interally creates a RoundRobinGroupChat with a single Assistant Agent that
    by default terminates itself when 8 internal messages are made OR 'TERMINATE' keyword
    is used.
    """
    internal_system_message = "You are a helpful AI assistant. Solve tasks using your tools. Send your response first and then reply with TERMINATE when the task has been completed."
    append_system_message = "Send your response first and then reply with TERMINATE when the task has been completed."
    def __init__(
        self,
        name: str,
        system_message: str,
        tools: List,
        model_client: ChatCompletionClient,
        description: Optional[str] = None,
        termination_condition: Optional[TerminationCondition] = None,
        model_client_stream: bool = False,
        reflect_on_tool_use: bool = False,
    ):
        self.name = name

        updated_system_message = ""
        if system_message and not termination_condition:
            # if system_message is provided but not termination condition, use default termination condition
            updated_system_message = f"{system_message}\n{self.append_system_message}"
        elif system_message and termination_condition:
            # if both system_message and termination condition are provided, use system_message
            updated_system_message = system_message
        else:
            # if both system_message and termination condition are not provided, use default internal_system_message
            updated_system_message = self.internal_system_message

        current_assistant = AssistantAgent(
            name=self.name,
            description=description or "An agent that provides assistance with ability to use tools.",
            system_message=updated_system_message,
            tools=tools,
            model_client=model_client,
            model_client_stream=model_client_stream,
            reflect_on_tool_use=reflect_on_tool_use,
        )

        if termination_condition is None:
            termination_condition = TextMentionTermination("TERMINATE") | MaxMessageTermination(max_messages=8)

        self.group_chat = RoundRobinGroupChat(
            participants=[current_assistant],
            termination_condition=termination_condition,
        )

    def get_instance(self):
        return self.group_chat
