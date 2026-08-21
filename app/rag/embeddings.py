from dotenv import load_dotenv
import os

from langchain_openai import OpenAIEmbeddings

# Load environment variables
load_dotenv()  # reads variables from a .env file and sets them in os.environ
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise RuntimeError("API key env variable missing")

EMBEDDING_MODEL_NAME = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536

embedding_model = OpenAIEmbeddings(
    model = EMBEDDING_MODEL_NAME,
    api_key = API_KEY
)


def embed_documents(texts: list[str])-> list[list[float]]:
    return embedding_model.embed_documents(texts)


def embed_query(query: str) -> list[float]:
    return embedding_model.embed_query(query)

