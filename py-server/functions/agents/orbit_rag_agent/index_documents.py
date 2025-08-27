import os
import sys
import re
from typing import List
from firebase_admin import firestore
from google.cloud.firestore_v1.vector import Vector

# Add the functions directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
functions_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.append(functions_dir)

from services.llm import create_embedding

def get_category(filepath: str) -> str:
    """Categorize file based on its path."""
    filename = os.path.basename(filepath).lower()
    if "token" in filename:
        return "token"
    if "company" in filename:
        return "company"
    if "roadmap" in filename:
        return "roadmap"
    if "tokenomics" in filename:
        return "tokenomics"
    if "orbit" in filename:
        return "orbit"
    if "protocol" in filename or "network" in filename or "supported" in filename:
        return "networks"
    return "other"

def read_file(path: str) -> str:
    """Read file content as text."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise

def _split_text(text: str, chunk_size: int = 200) -> List[str]:
    """Split plain text into fixed-size chunks."""
    text = re.sub(r"\s+", " ", text).strip()  # Normalize whitespace
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

async def index_documents(sources: List[str], collection_name: str = "orbit_docs") -> int:
    """
    Index multiple documents into Firestore with vector embeddings in chunks.
    """
    db = firestore.client()
    collection = db.collection(collection_name)
    total_chunks = 0
    batch = db.batch()
    batch_count = 0

    for source in sources:
        try:
            if not os.path.exists(source):
                continue

            content = read_file(source)
            category = get_category(source)
            chunks = _split_text(content, chunk_size=200)

            for i, chunk in enumerate(chunks):
                embedding = await create_embedding(chunk)
                doc_data = {
                    "content": chunk,
                    "metadata": {
                        "source": os.path.basename(source),
                        "category": category,
                        "chunk_index": i,
                    },
                    "embedding_field": Vector(embedding),
                    "timestamp": firestore.SERVER_TIMESTAMP,
                }

                doc_ref = collection.document()
                batch.set(doc_ref, doc_data)
                batch_count += 1
                total_chunks += 1

                if batch_count >= 500:
                    batch.commit()
                    batch = db.batch()
                    batch_count = 0

        except Exception as e:
            print(f"Error indexing {source}: {e}")
            continue

    if batch_count > 0:
        batch.commit()

    return total_chunks

async def main():
    """Main function to run the indexing process."""
    # Define document sources
    base_path = os.path.dirname(os.path.abspath(__file__))
    sources = [
        os.path.join(base_path, "docs", "company.txt"),
        os.path.join(base_path, "docs", "orbit.txt"),
        os.path.join(base_path, "docs", "roadmap.txt"),
        os.path.join(base_path, "docs", "token.txt"),
        os.path.join(base_path, "docs", "tokenomics.txt"),
        os.path.join(base_path, "docs", "supported_networks.txt"),
    ]

    try:
        await index_documents(sources)
    except Exception as e:
        raise e

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 