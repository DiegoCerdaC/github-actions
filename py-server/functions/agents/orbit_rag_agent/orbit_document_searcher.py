from typing import List
from firebase_admin import firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from services.llm import create_embedding

class OrbitDocumentSearcher:
    """Simple document indexer that embeds entire files."""

    def __init__(self, collection_name: str = "orbit_docs") -> None:
        db = firestore.client()
        self.collection = db.collection(collection_name)

    async def search_similar(self, query: str, limit: int = 10) -> List[str]:
        """Get documents similar to the provided query using Firestore's vector search."""
        try:
            # Generate query embedding
            query_embedding = await create_embedding(query)
            
            # Use Firestore's vector search with find_nearest
            vector_query = self.collection.find_nearest(
                vector_field="embedding_field",
                query_vector=Vector(query_embedding),
                distance_measure=DistanceMeasure.EUCLIDEAN,
                limit=limit,
            )
            
            results = vector_query.get()
            
            # Process results to return only content
            return [doc.to_dict().get("content", "") for doc in results]
            
        except Exception as e:
            return []