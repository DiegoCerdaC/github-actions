from utils.firebase import db, get_request_ctx
from firebase_admin import firestore
from firebase_admin.firestore import DocumentReference

# Collection and field constants
ANALYTICS_COLLECTION = "analytics"
USERS_DOCUMENT = "users"
GLOBAL_DOCUMENT = "global"
ANALYTICS_DOCUMENT = "analytics"
AGENTS_USED_FIELD = "agents_used"
TOTAL_MESSAGES_FIELD = "total_messages"
UPDATED_AT_FIELD = "updated_at"


def increment_field_in_doc(
    doc_ref: DocumentReference, field: str, key: str | None = None, amount: int = 1
):
    """
    Increments a field within a document. If the document does not exist, creates it.

    Args:
        doc_ref: Document Reference.
        field: Name of the field (or subfield) to increment.
        key: Optional key if the field is a map (like agents_used).
        amount: Value of the increment.
    """
    doc = doc_ref.get()
    full_field = f"{field}.{key}" if key else field
    if not doc.exists:
        # Create initial document
        doc_ref.set(
            {
                field: {key: amount} if key else amount,
                UPDATED_AT_FIELD: firestore.SERVER_TIMESTAMP,
            }
        )
    else:
        updates = {
            full_field: firestore.Increment(amount),
            UPDATED_AT_FIELD: firestore.SERVER_TIMESTAMP,
        }
        doc_ref.update(updates)


def increment_agent_used(agent: str, chat_id: str):
    try:
        # Global
        global_doc_ref = db.collection(ANALYTICS_COLLECTION).document(GLOBAL_DOCUMENT)
        increment_field_in_doc(global_doc_ref, AGENTS_USED_FIELD, key=agent)

        # User
        user_id = get_request_ctx(parentKey=chat_id, key="user_id")
        if user_id:
            user_analytics_doc = (
                db.collection(ANALYTICS_COLLECTION)
                .document(USERS_DOCUMENT)
                .collection(user_id)
                .document(ANALYTICS_DOCUMENT)
            )
            increment_field_in_doc(user_analytics_doc, AGENTS_USED_FIELD, key=agent)
    except Exception as e:
        print("Error Updating Orbit Agents Used Analytics", e)


def increment_message_count(chat_id: str):
    try:
        # Global
        global_doc_ref = db.collection(ANALYTICS_COLLECTION).document(GLOBAL_DOCUMENT)
        increment_field_in_doc(global_doc_ref, TOTAL_MESSAGES_FIELD)

        # User
        user_id = get_request_ctx(parentKey=chat_id, key="user_id")
        if user_id:
            user_analytics_doc = (
                db.collection(ANALYTICS_COLLECTION)
                .document(USERS_DOCUMENT)
                .collection(user_id)
                .document(ANALYTICS_DOCUMENT)
            )
            increment_field_in_doc(user_analytics_doc, TOTAL_MESSAGES_FIELD)
    except Exception as e:
        print("Error Updating Message Count Analytics", e)
