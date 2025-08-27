from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from typing import Annotated
from utils.firebase import (
    get_enso_supported_chains_and_protocols,
)

from services.llm import gpt_4o_client

from agents.enso.enso_functions import (
    defi_quote,
)
import services.analytics as analytics
from services.tracing import set_status_ok, set_status_error, tracer, set_attributes


@tracer.start_as_current_span("enso_agent")
async def call_enso_agent(
    task: str, chat_id: str, use_frontend_quoting: bool = True
) -> Annotated[str, "The chat history of the Enso agent."]:
    """
    Executes a specific task using the Enso protocol, leveraging AI capabilities for enhanced decision-making.

    Parameters:
    - task (str): A textual query describing the task to be executed, including any necessary parameters or conditions.
    - chat_id (str): The current chat id

    Returns:
    - str: The AI agent's response, detailing the outcome of the task execution or any errors encountered.

    The Enso agent is designed to:
    - Analyze the task and determine the appropriate actions using the Enso protocol.
    - Provide clear feedback on the task execution, including any necessary confirmations or error messages.
    - Ensure that all interactions are logged and monitored for quality assurance.
    """
    analytics.increment_agent_used("enso", chat_id)
    set_attributes(
        {"chat_id": chat_id, "task": task, "use_frontend_quoting": use_frontend_quoting}
    )

    supported_chains_and_protocols = get_enso_supported_chains_and_protocols()

    enso_agent = AssistantAgent(
        name="enso",
        system_message=f"""
        You are a helpful assistant that can perform defi transactions using the Enso protocol. You can perform transactions between two types of tokens: base tokens and defi tokens. 
        
        The following chains and protocols are supported:
        {supported_chains_and_protocols}
        
        IMPORTANT: When users specify protocols, correct obvious spelling mistakes (like "avee" → "aave") but keep the protocol name as they intended. Don't change "aave" to "aave-v3" or "morpho" to "morpho-blue-vaults" - just fix spelling errors and use what they meant.
        Example if the user mentions as protocol 'unixswap', you should correct it to 'uniswap' and use it as the protocol name.
        Another example, user mentions 'compaund' you should correct it to 'compound' and use it as the protocol name.
        Be smart when identifying the protocol name and correct spelling mistakes the user could make.
        Users can also use 'partial' or 'different-way' to mention a protocol. Example 'aave' would match with 'aave-v3' and 'aave-v2'. So it's OK even if it's not a strict match.
        Use this logic for every supported protocol whenever the user mentions a protocol.
        
        If the user specifies a chain or protocol that is not supported, reply explaining briefly indicationg the supported chains and protocols.
        If no chain or protocol is specified, call the defi_quote function with 'None' as the chain and protocol parameters.
        Base tokens are common ERC20 and native tokens, like USDC, USDT, WETH, etc. Defi tokens represent positions in defi protocols, like aUSDC which represents a USDC position from aave-v2 on Ethereum or cbETH/rETH/wstETH which represents a position on a balancer-v2 pool for staked ether on Arbitrum.
        You must identify clearly if the user is trying to make a deposit or a withdrawal.
        Be smart when identifying the token (base token, like ERC20 or native token) and the defi token (like aUSDC, cbETH, rETH, wstETH, etc).
        If the user doesn't specify the token (base token), use USDC as default.
        Only call the function 'defi_quote' ONE time per user intent.
        The current chat id is {chat_id}. And use_frontend_quoting is ALWAYS {use_frontend_quoting}.
        After completing your task just reply TERMINATE.
        The function can return a message indicating the process has started or an error message.
        If non-sense tasks / questions are incoming, just reply indication you can only help with DeFi transactions.
        If a function throws an error, reply with the error message and the word TERMINATE.
        """,
        model_client=gpt_4o_client,
        reflect_on_tool_use=False,
        tools=[defi_quote],
    )

    updated_task = f"""
        The user asked for this task: ''{task}''.
        Use the function 'defi_quote' with the required parameters:
        - token: The token address or symbol to deposit from or withdraw to. (if not specified, use USDC as default)
        - chat_id: The current chat id.
        - is_withdraw: Whether to withdraw or deposit. (if the user doesn't specify, use False by default)
        
        If the user specifies also the from chain, protocol or defi_token_symbol, pass them as parameters to the function.
        - amount: The amount of the token to deposit or withdraw.
        - from_chain: The chain name (optional).
        - protocol: The protocol name (optional). Don't modify the protocol name or add any extra characters to it. Only fix any misspelling errors of the protocol name and use pass it to the function as it is (or with the misspelling fixed).
        - defi_token_symbol: The DeFi token symbol (optional) to deposit to or withdraw from.
        
        The current chat id is {chat_id}. And use_frontend_quoting is ALWAYS {use_frontend_quoting}.
        Reply TERMINATE after sending a reply to the user so the front desk agent can forward the message.
    """
    try:
        chat_result = await enso_agent.on_messages(
            messages=[TextMessage(content=updated_task, source="user")],
            cancellation_token=CancellationToken(),
        )
        set_status_ok()
        return chat_result.chat_message.content
    except Exception as e:
        set_status_error(e)
        return f"An error occurred: {str(e)}"
