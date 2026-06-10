import os
from pathlib import Path
from ragas.testset import TestsetGenerator
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from ragas.run_config import RunConfig
from dotenv import load_dotenv
from app.rag.load_documents import load_documents
from app.rag.split_documents import split_docs_chunks


# Load environment variables

load_dotenv()  # reads variables from a .env file and sets them in os.environ
api_key = os.getenv("API_KEY")


BASE_DIR = Path(__file__).resolve().parent  # app/rag_evals


generator_llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=api_key,
    temperature=0
)

generator_embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=api_key
)



generator = TestsetGenerator.from_langchain(
    llm=generator_llm,
    embedding_model=generator_embeddings
)


docs = split_docs_chunks()
docs = docs[:10]

run_config = RunConfig(
    max_retries=10,
    max_wait=120,
    timeout=300,
    max_workers=1
)


testset = generator.generate_with_langchain_docs(
    docs,
    testset_size=5,
    run_config=run_config
)

df = testset.to_pandas()

os.makedirs("evaluation", exist_ok=True)

df.to_csv(
    BASE_DIR/"testset.csv",
    index=False
)

print(df.head())
print(df.columns.tolist())



