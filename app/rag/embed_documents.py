from pathlib import Path
import faiss

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI



# Folder(eng/finance)->Load files->MarkdownHeaderTextSplitter(per file)-> Attach Metadata(domain+file+headers)->Embeddings->VectorDB(with filters)
# Step1: Load Markdown files

base_path = Path("../../resources/data")

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
    return docs  # Return the full list after processing all files


all_documents = get_documents()
print(f"Loaded {len(all_documents)} Markdown files.")

# Step2: Splitting documents into chunks. Splitting markdown files by headers