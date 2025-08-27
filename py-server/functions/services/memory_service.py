from typing import List, Dict, Any, Optional
from firebase_admin import firestore
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1.vector import Vector
from services.llm import create_embedding
from agents.info_extraction_agent import extract_information_agent
import logging


class MemoryService:
    def __init__(self):
        self.db = firestore.client()
        self.logger = logging.getLogger(__name__)

    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for the given text.
        """
        try:
            embedding = await create_embedding(text)
            # Ensure embedding is a list of floats
            if not isinstance(embedding, list):
                embedding = list(embedding)

            # Verify all elements are floats
            if not all(isinstance(x, float) for x in embedding):
                embedding = [float(x) for x in embedding]

            return embedding
        except Exception as e:
            self.logger.error(f"Error generating embedding: {str(e)}")
            raise

    async def record_memory(
        self,
        user_id: str,
        content: str,
        agent_response: str,
        items: List[Dict[str, Any]],
        reasoning: Optional[str] = None,
        type: str = "interaction",
        chat_id: Optional[str] = None,
    ) -> str:
        """
        Record a user memory with monitoring. Generates embedding, checks for similar memories,
        and stores the memory if it's unique enough.
        """
        try:
            # Generate embedding for new memory
            embedding = await self._generate_embedding(content)

            # Check for similar existing memories
            similar_memories = await self.get_similar_memories(
                user_id=user_id,
                embedding=embedding,
                limit=1,  # We only need to check the most similar one
            )

            # If we found a similar memory with a small distance, return its ID instead of creating a new one
            if (
                similar_memories and similar_memories[0].get("distance", 1.0) < 0.45
            ):  # Threshold for similarity
                doc_id = similar_memories[0].get("id", None)
                if doc_id:
                    # Update the document and increment the similarity_count
                    self.db.collection("memories").document(doc_id).update({
                        "similarity_count": firestore.Increment(1),
                        "last_updated": firestore.SERVER_TIMESTAMP,
                    })
                return

            # Generate a new memory ID
            memory_id = self.db.collection("memories").document().id

            # Create memory data with embedding using Vector class
            memory_data = {
                "id": memory_id,
                "user_id": user_id,
                "content": content,
                "agent_response": agent_response,
                "items": items,
                "reasoning": reasoning,
                "type": type,
                "chat_id": chat_id,
                "embedding_field": Vector(embedding),  # Convert list to Vector
                "timestamp": firestore.SERVER_TIMESTAMP,
                "similarity_count": 0,
            }

            # Store the memory directly in the memories collection
            self.db.collection("memories").document(memory_id).set(memory_data)

            return memory_id
        except Exception as e:
            self.logger.error(f"Error recording memory: {str(e)}")
            raise

    async def get_similar_memories(
        self, user_id: str, embedding: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get memories similar to the provided embedding using Firestore's vector search."""
        try:
            # Use Firestore's vector search with find_nearest on the memories collection
            memories_ref = self.db.collection("memories")

            vector_query = memories_ref.where(filter=FieldFilter("user_id", "==", user_id)).find_nearest(
                vector_field="embedding_field",
                query_vector=Vector(embedding),
                distance_measure=DistanceMeasure.EUCLIDEAN,
                limit=limit,
                distance_result_field="vector_distance",
                distance_threshold=0.75,
            )
            memories_snapshot = vector_query.get()

            memories = []
            for doc in memories_snapshot:
                doc_data = doc.to_dict()
                memories.append(
                    {
                        "id": doc.id,
                        "content": doc_data.get("content", ""),
                        "agent_response": doc_data.get("agent_response", ""),
                        "items": doc_data.get("items", []),
                        "type": doc_data.get("type", ""),
                        "reasoning": doc_data.get("reasoning"),
                        "chat_id": doc_data.get("chat_id"),
                        "user_id": doc_data.get("user_id"),
                        "distance": doc_data.get("vector_distance", 0.0),
                    }
                )

            return memories
        except Exception as e:
            self.logger.error(f"Error getting similar memories: {str(e)}")
            return []

    async def get_relevant_memories(
        self, user_id: str, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get relevant memories with performance monitoring.
        """
        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)

            # Get similar memories using Firestore's vector search
            similar_memories = await self.get_similar_memories(
                user_id=user_id, embedding=query_embedding, limit=limit
            )

            self.logger.info(f"Found {len(similar_memories)} relevant memories")
            return similar_memories
        except Exception as e:
            self.logger.error(f"Error getting relevant memories: {str(e)}")
            return []

    async def store_message_memory(
        self, user_id: str, content: str, agent_response: str, chat_id: str
    ) -> None:
        """
        Extracts key information from user messages and stores it in the memory database
        if the message contains relevant data.

        Args:
            snapshot_data: The message data from Firestore
            chat_id: The ID of the chat
            user_id: The ID of the user
        """
        # Extract information form user input
        extracted_info = await extract_information_agent(content)

        # Check if extracted_info has any items
        has_relevant_info = len(extracted_info.items) > 0

        # Record the interaction if there is content and relevant information
        if content and has_relevant_info:
            # Convert extracted_info to dict for storage
            extracted_info_dict = extracted_info.dict()

            memory_type = (
                "user_preference"
                if any(
                    item.get("type") == "user_preference"
                    for item in extracted_info_dict["items"]
                )
                else "interaction"
            )

            await self.record_memory(
                user_id=user_id,
                content=content,
                agent_response=agent_response,
                items=extracted_info_dict["items"],
                reasoning=extracted_info_dict.get("reasoning"),
                type=memory_type,
                chat_id=chat_id,
            )

    async def get_agent_memory_context(self, user_id: str, task: str) -> str:
        """
        Get relevant memory context for an agent based on the task.
        Args:
            user_id: User ID
            task: Current task
        Returns:
            str: Formatted memory context
        """
        # Get all recent interactions first
        relevant_memories = await self.get_relevant_memories(
            user_id=user_id,
            query=task,
            limit=10,  # Get more interactions to find better matches
        )

        # Process and format the memories for better accessibility
        if relevant_memories:
            processed_memories = []
            for memory in relevant_memories:
                if isinstance(memory, dict):
                    content = memory.get("content", "")
                    agent_response = memory.get("agent_response", "")
                    items = memory.get("items", [])

                    # Group items by type
                    preferences = []
                    interactions = []

                    for item in items:
                        if item.get("type") == "user_preference":
                            preferences.append(item.get("content", ""))
                        elif item.get("type") == "interaction":
                            interactions.append(item.get("content", ""))

                    # Format the information
                    if preferences:
                        processed_memories.append(
                            f"User Preferences: {', '.join(preferences)}"
                        )
                    if interactions:
                        processed_memories.append(
                            f"Past Interactions: {', '.join(interactions)}"
                        )
                    if content:
                        processed_memories.append(f"User Message: {content}")
                    if agent_response:
                        processed_memories.append(f"Agent Response: {agent_response}")

            return "\n".join(processed_memories)

        return relevant_memories
