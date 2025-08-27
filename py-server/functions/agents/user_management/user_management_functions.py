from typing import Annotated
from firebase_admin import firestore
from utils.firebase import db


VALID_FIELDS = {"name", "risk_profile", "onboarding_completed"}
VALID_RISK_LEVELS = {"STABLE", "RISKY", "DEGEN"}
VALID_ONBOARDING_STATUSES = {"ONBOARDED", "NOT_ONBOARDED"}


def update_user(
    user_id: Annotated[str, "The user's ID"],
    updates: Annotated[
        dict,
        "The updates to the user's profile: name: str, risk_profile: str, onboarding_completed: str",
    ],
) -> str:
    """Updates one or multiple fields in the user's profile
    Args:
        user_id: The user's ID
        updates: The updates to the user's profile: name: str, risk_profile: str, onboarding_completed: str
    Returns:
        A message indicating the success or failure of the update
    Raises:
        ValueError: If the user_id is not provided, if no fields are provided to update, if the fields provided are invalid, or if the risk level is not valid.
    """
    try:
        if not user_id:
            raise ValueError("user_id is required")

        if not updates:
            raise ValueError("No fields provided to update.")

        invalid_fields = [field for field in updates if field not in VALID_FIELDS]
        if invalid_fields:
            raise ValueError(f"Invalid fields: {', '.join(invalid_fields)}")

        if (
            "risk_profile" in updates
            and updates["risk_profile"] not in VALID_RISK_LEVELS
        ):
            raise ValueError(
                f"Invalid risk level. Must be one of: {', '.join(VALID_RISK_LEVELS)}"
            )

        if (
            "onboarding_completed" in updates
            and updates["onboarding_completed"] not in VALID_ONBOARDING_STATUSES
        ):
            raise ValueError(
                f"Invalid onboarding completed value. Must be one of: {', '.join(VALID_ONBOARDING_STATUSES)}"
            )

        update_user_profile(user_id, updates)

        return f"Successfully updated user profile."
    except Exception as e:
        return f"Error updating profile: {str(e)}"


def update_user_profile(user_id: str, updates: dict):
    user_ref = db.collection("users").document(user_id)
    user_ref.update(updates)


async def add_onboarding_ui_message(
    chat_id: Annotated[str, "The chat_id"],
    user_id: Annotated[str, "The user_id"],
    component: Annotated[
        str, "The component to add to the onboarding UI"
    ] = "risk_profile",
):
    """Adds an onboarding UI message in the chat with the chat_id and user_id"""
    try:
        messages_ref = db.collection("chats").document(chat_id).collection("messages")
        timestamp = firestore.SERVER_TIMESTAMP
        new_message = {
            "component": component,
            "createdAt": timestamp,
            "sender": "ui",
            "userId": user_id,
            "updatedAt": timestamp,
            "messageType": "ui",
        }
        messages_ref.add(new_message)
        return "Onboarding UI sent. Please select the risk profile."
    except Exception as error:
        raise error
