from dotenv import load_dotenv
import os

from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from .split_documents import split_docs_chunks


# Load environment variables
load_dotenv()  # reads variables from a .env file and sets them in os.environ
api_key = os.getenv("API_KEY")

client = ChatOpenAI(model="gpt-4.1-mini", temperature=0, api_key=api_key)


# Step3: Create Embeddings and Fiass vector store
def create_vector_store():
    """Create embeddings and vector store"""

    chunks = split_docs_chunks()

    # create embeddings model
    embeddings_model = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=api_key
    )

    vector_store = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings_model
    )

    return vector_store


#print(create_vector_store)