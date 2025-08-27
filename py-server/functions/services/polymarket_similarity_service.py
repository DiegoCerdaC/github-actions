from typing import List, Dict, Any, Optional
from firebase_admin import firestore
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google.cloud.firestore_v1.vector import Vector
from services.llm import create_embedding
import logging


class PolymarketSimilarityService:
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

    async def check_similar_event_exists(
        self, title: str, similarity_threshold: float = 0.35
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a similar event already exists in the rumours_events collection.

        Args:
            title: The title of the event to check
            similarity_threshold: Threshold for considering events similar (lower = more strict)

        Returns:
            Optional[Dict]: Similar event data if found, None otherwise
        """
        try:
            # Generate embedding for the new event title
            event_text = f"{title}".strip()
            embedding = await self._generate_embedding(event_text)

            # Search for similar events in rumours_events collection that are pending
            rumours_ref = self.db.collection("rumours_events").where(
                "tradeStatus", "==", "pending"
            )

            vector_query = rumours_ref.find_nearest(
                vector_field="title_embedding",
                query_vector=Vector(embedding),
                distance_measure=DistanceMeasure.EUCLIDEAN,
                limit=1,  # We only need the most similar one
                distance_result_field="vector_distance",
                distance_threshold=similarity_threshold,
            )

            similar_events = vector_query.get()

            if similar_events:
                most_similar = similar_events[0]
                doc_data = most_similar.to_dict()
                distance = doc_data.get("vector_distance", 1.0)

                return {
                    "id": most_similar.id,
                    "title": doc_data.get("title", ""),
                    "distance": distance,
                    "original_event_id": doc_data.get("original_event_id", ""),
                }

            return None

        except Exception as e:
            self.logger.error(f"Error checking for similar events: {str(e)}")
            return None

    async def save_event_with_embedding(
        self,
        event_id: str,
        event_data: Dict[str, Any],
    ) -> bool:
        """
        Save an event to the rumours_events collection with its title embedding.

        Args:
            event_id: The ID for the new event
            event_data: The complete event data to save

        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Generate embedding for the title
            event_text = f"{event_data['title']}".strip()
            embedding = await self._generate_embedding(event_text)

            # Add embedding to event data
            event_data["title_embedding"] = Vector(embedding)

            # Save to rumours_events collection
            self.db.collection("rumours_events").document(event_id).set(event_data)

            self.logger.info(f"Successfully saved event {event_id} with embedding")
            return True

        except Exception as e:
            self.logger.error(f"Error saving event with embedding: {str(e)}")
            return False
