from typing import Dict, Union, TypeVar
from services.scheduler import scheduler_service, ScheduledTask
from utils.firebase import get_request_ctx, save_ui_message, save_agent_thought

# Allowed transaction types for scheduled tasks
ALLOWED_TRANSACTION_TYPES = {
    "STAKE",
    "BRIDGE",
    "SWAP",
    "DEPOSIT",
    "TRANSFER",
    "RELOCATE",
    "CLAIM_FEES",
}

TransactionType = TypeVar("TransactionType", bound=str)


def get_user_scheduled_tasks(
    chat_id: str,
) -> Union[str, Dict[str, list[ScheduledTask]]]:
    """
    Get all scheduled tasks for a user.
    Args:
        chat_id (str): The current chat_id
    Returns:
        dict: Response containing tasks and status

    Example prompts:
        - "Show me all my scheduled tasks"
        - "What tasks do I have scheduled?"
        - "List my scheduled tasks"
    """
    try:
        user_id = get_request_ctx(chat_id, "user_id")
        if not user_id:
            return "Current User not found. Please login again."
        save_agent_thought(
            chat_id=chat_id, thought="Retrieving all scheduled tasks for user"
        )
        response = scheduler_service.get_user_scheduled_tasks(user_id)
        user_tasks = response.get("tasks", [])
        if not user_tasks:
            return "You don't have any scheduled tasks"
        save_ui_message(
            chat_id=chat_id,
            component="scheduled_tasks",
            renderData={"tasks": user_tasks},
        )

        return "Process to fetch current scheduled tasks initiated"
    except Exception as e:
        return f"Error fetching scheduled tasks: {e}"


def create_scheduled_task(
    description: str,
    chat_id: str,
    interval: int,
    transaction_type: TransactionType,
):
    """
    Create a new scheduled task.
    Args:
        description (str): The task description. Should include all the necessary information for the task to be executed.
        For example for staking, should include the amount, the token, and the chain.
        Another example, for swaps or bridges, should include amount, tokens, chains, etc.
        chat_id (str): The chat id
        interval (int): Interval in minutes for task execution (Ex: 1 hour = 60, 1 day = 1440)
        transaction_type (str): Type of transaction (STAKE, BRIDGE, SWAP, DEPOSIT, RELOCATE, CLAIM_FEES)
    Returns:
        dict: Response containing taskId and status

    Example prompts:
        - "Schedule a task to check my balance every 30 minutes"
        - "Create a new recurring task to send ETH daily"
        - "Set up an automated task that runs every hour"
    """
    user_id = get_request_ctx(chat_id, "user_id")
    if not user_id:
        return "Current User not found. Please login again."
    if interval < 5:
        return "The minimum interval to schedule a task is 5 minutes"

    if transaction_type not in ALLOWED_TRANSACTION_TYPES:
        return f"Invalid transaction type. You can only schedule tasks for: {', '.join(ALLOWED_TRANSACTION_TYPES.__args__)}"

    save_agent_thought(chat_id=chat_id, thought="Creating new scheduled task")
    result = scheduler_service.schedule_new_task(
        description=description, user_id=user_id, interval=interval
    )
    if result.get("status") == "success":
        save_agent_thought(
            chat_id=chat_id, thought="Scheduled task created successfully"
        )
        save_ui_message(
            chat_id=chat_id,
            component="schedule_details",
            renderData={
                "taskId": result.get("taskId"),
                **result.get("details", {}),
                "status": result.get("status"),
            },
        )
        return f"Task created successfully with ID: {result.get('taskId')}"
    else:
        save_agent_thought(
            chat_id=chat_id, thought="Scheduled task failed to be created"
        )
        return f"Failed to create task: {result.get('errors')}"


def delete_scheduled_task(chat_id: str, task_id: list[str] | None = None):
    """
    Delete a specific scheduled task.
    Args:
        chat_id (str): The current chat_id
        task_id (str | None) (optional): ID of the task to delete or None if the user doesn't specify the task id
    Returns:
        dict: Response containing status

    Example prompts:
        - "Remove task number 123"
        - "Delete the scheduled task with ID xyz"
        - "I want to stop a task that I have scheduled/running"
        - "Can we disable a schedule task?"
        - "I want to delete a scheduled task"
    """
    user_id = get_request_ctx(chat_id, "user_id")
    if not user_id:
        return "Current User not found. Please login again."
    if not task_id:
        save_agent_thought(
            chat_id=chat_id, thought="Deleting all scheduled tasks for user"
        )
        response = scheduler_service.get_user_scheduled_tasks(user_id)
        user_tasks = response.get("tasks", [])
        if not user_tasks:
            return "You don't have any scheduled tasks"
        save_ui_message(
            chat_id=chat_id,
            component="scheduled_tasks",
            renderData={"tasks": user_tasks},
        )
        return "Please select the task you want to delete and click the Trash button."

    save_agent_thought(
        chat_id=chat_id, thought=f"Deleting scheduled task {task_id} for user"
    )
    result = scheduler_service.delete_scheduled_tasks(task_id, user_id)
    if result.get("status") == "success":
        return f"Task deleted successfully"
    else:
        return f"Failed to delete task: {result.get('errors')}"


def delete_all_scheduled_tasks(chat_id: str):
    """
    Delete all scheduled tasks for a user.
    Args:
        chat_id (str): The current chat_id
    Returns:
        dict: Response containing status

    Example prompts:
        - "Delete all my scheduled tasks"
        - "Remove all my automated tasks"
        - "Clear my task list"
    """
    user_id = get_request_ctx(chat_id, "user_id")
    if not user_id:
        return "Current User not found. Please login again."
    response_user_tasks = scheduler_service.get_user_scheduled_tasks(user_id)
    user_tasks = response_user_tasks.get("tasks", [])
    if not user_tasks:
        return "You don't have any scheduled tasks"
    save_agent_thought(chat_id=chat_id, thought="Deleting all scheduled tasks for user")
    result = scheduler_service.delete_scheduled_tasks([], user_id)
    if result.get("status") == "success":
        return f"All tasks deleted successfully"
    else:
        return f"Failed to delete tasks: {result.get('errors')}"
