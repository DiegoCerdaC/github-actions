import requests
from typing import Dict, TypedDict
from config import FIREBASE_SERVER_ENDPOINT
from datetime import datetime


class ScheduledTask(TypedDict):
    createdAt: datetime
    description: str
    evm_wallet_address: str
    interval: int
    lastRun: datetime
    sol_wallet_address: str
    taskId: str
    userId: str


class SchedulerService:
    def __init__(self):
        self.base_url = FIREBASE_SERVER_ENDPOINT

    def get_user_scheduled_tasks(self, user_id: str) -> Dict[str, list[ScheduledTask]]:
        """
        Get all scheduled tasks for a user.
        Args:
            user_id (str): User id
        Returns:
            dict: Response containing tasks and status
        Raises:
            requests.RequestException: If there is an error in the request
        """
        try:
            response = requests.get(
                f"{self.base_url}/getUserScheduledTasks", params={"userId": user_id}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            return e.response.json()
        except requests.RequestException as e:
            raise e
        except Exception as e:
            raise e

    def schedule_new_task(
        self,
        description: str,
        user_id: str,
        interval: int,
    ):
        """
        Create a new scheduled task.
        Args:
            description (str): The task description
            user_id (str): The user id
            interval (int): Interval in minutes for task execution
        Returns:
            dict: Response containing taskId and status
        Raises:
            requests.RequestException: If there is an error in the request
        """
        data = {"description": description, "userId": user_id, "interval": interval}

        try:
            response = requests.post(f"{self.base_url}/createScheduledTask", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            return e.response.json()
        except requests.RequestException as e:
            raise e
        except Exception as e:
            raise e

    def delete_scheduled_tasks(self, task_ids: list[str] | None, user_id: str):
        """
        Delete a specific scheduled task.
        Args:
            task_id (str): ID of the task to delete
            user_id (str): The user id
        Returns:
            dict: Response containing status
        Raises:
            requests.RequestException: If there is an error in the request
        """

        data = {"taskIds": task_ids, "userId": user_id}

        try:
            response = requests.post(
                f"{self.base_url}/deleteUserScheduledTasks", json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            return e.response.json()
        except requests.RequestException as e:
            raise e
        except Exception as e:
            raise e


scheduler_service = SchedulerService()
