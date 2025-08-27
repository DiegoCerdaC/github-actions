from config import OPENAI_API_KEY
from autogen_ext.models.openai import OpenAIChatCompletionClient
from openai import AsyncOpenAI

gpt_4o_client = OpenAIChatCompletionClient(
    model="gpt-4o", api_key=OPENAI_API_KEY, temperature=0.0, seed=None
)
gpt_4o_mini_client = OpenAIChatCompletionClient(
    model="gpt-4o-mini", api_key=OPENAI_API_KEY, temperature=0.0, seed=None
)

# Create OpenAI client for embeddings
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def create_embedding(text: str) -> list[float]:
    """Create an embedding using OpenAI's text-embedding-3-small model."""
    response = await openai_client.embeddings.create(
        model="text-embedding-3-small", input=text
    )
    return response.data[0].embedding
