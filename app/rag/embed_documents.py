from dotenv import load_dotenv
from pathlib import Path
import os
import faiss

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI


# Load environment variables

load_dotenv()  # reads variables from a .env file and sets them in os.environ
api_key=os.getenv("API_KEY")

client = ChatOpenAI(model="gpt-4.1-mini", temperature=0,api_key=api_key)


# Folder(eng/finance)->Load files->MarkdownHeaderTextSplitter(per file)-> Attach Metadata(domain+file+headers)->Embeddings->VectorDB(with filters)
# Step1: Load Markdown files

#base_path = Path("../../resources/data")
# Instead of relative path, use absolute path
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Adjust levels to project root
base_path = BASE_DIR / "resources" / "data"

# Traverse all folders
def get_documents():
    """Read Markdown documents from resources folder and attach metadata"""
    docs = []

    # Traverse all Markdown files recursively
    for file_path in base_path.rglob("*.md"):
        domain = file_path.parent.name  # engineering/finance/hr/marketing
        text = file_path.read_text(encoding="utf-8")

        docs.append(
            Document(
                page_content=text,
                metadata={
                    "domain": domain,
                    "source": file_path.name,
                    "path": str(file_path)
                }
            )
        )

    if not docs:
        raise FileNotFoundError(f"No Markdown files found in {base_path}")

    return docs  # Return the full list after processing all files


all_documents = get_documents()
print(f"Loaded {len(all_documents)} Markdown files.")

# Step2: Splitting documents into chunks. Splitting markdown files by headers

headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

def split_documents_chunks():
    """Splits the loaded documents into chunks"""

    all_chunks = []
    docs = get_documents()
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=True)

    for doc in docs:
        chunks = markdown_splitter.split_text(doc.page_content)

        if not chunks:
            raise ValueError("No documents found. Check your base_path and .md files.")

        for chunk in chunks:
            content = chunk.page_content if isinstance(chunk, Document) else str(chunk)
            all_chunks.append(Document(page_content=content, metadata=doc.metadata.copy()))

    return all_chunks


# Step3: Create Embeddings and vector store

def create_vector_store():
    """Create embeddings and vector store"""

    chunks = split_documents_chunks()

    #create embeddings model
    embeddings_model = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=api_key
    )
    embedding_dim = len(embeddings_model.embed_query("test"))


    index = faiss.IndexFlatL2(embedding_dim)

    vector_store = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings_model
    )

    return vector_store

# Build vector store once on import/startup
vector_store = create_vector_store()

# User Query
#query = "What is FinSolve Technologies's revenue growth in 2024?"
#query = "What is python?"
#query = "What is software development lifecycle?"
query = "Which department has more expenses in 2024?"


# Run a semantic search
def semantic_search(vector_store):
    """Runs a semantic search and retrieves top 3 results"""

    results = vector_store.similarity_search(query=query, k=3)

    for i, doc in enumerate(results, start=1):
        print(f"\n---Result{i}---")
        print(doc.page_content)
        print(doc.metadata)

    # Build a clean context from top-3 chunks
    context = "\n\n".join(
        f"""
    Source: {doc.metadata['source']}
    Section: {doc.metadata.get('Header 3', 'N/A')}
    Content:
    {doc.page_content}
    """.strip()
        for doc in results
    )
    return context


def get_response():
    """Returns API response"""

    context = semantic_search(vector_store)

    # User prompt
    prompt = f"""
    You are a technical documentation expert. Act as a kind and respectful assistant for a company.
    Answer the question using only the information provided in the context.
    - Be concise and exact
    - If the answer is too long, summarize  into four or five sentences. Otherwise provide the answer in one or two sentences.
    - Each sentence should be a new line
    - Use bullet points if appropriate
    -Do not add external knowledge and do not hallucinate
    - If the answer is not fully present, say "Information not provided in the documents."
    - If the answer is present answer in the following format.
    user: What is the revenue growth in 2024?
    system: The revenue growth in 2024 is 28%
    
    user: What are client applications?
    system: The client applications are Mobile,web or API interfaces.
    
    
    Context:
    {context}
    
    Question:
    {query}
    """

    # generate answer
    response = client.invoke(prompt)

    # Print structured output
    return " ".join(str(response.content).replace("-", "").split())


print("API Response", get_response())



