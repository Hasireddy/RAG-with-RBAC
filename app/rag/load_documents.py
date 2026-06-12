from dotenv import load_dotenv
from pathlib import Path
import os

from langchain_core.documents import Document
from langchain_community.document_loaders import CSVLoader, TextLoader
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_openai import ChatOpenAI

# Load environment variables

load_dotenv()  # reads variables from a .env file and sets them in os.environ
api_key = os.getenv("API_KEY")


client = ChatOpenAI(model="gpt-4.1-mini", temperature=0, api_key=api_key)


# Folder(eng/finance)->Load files->MarkdownHeaderTextSplitter(per file)-> Attach Metadata(domain+file+headers)->Embeddings->VectorDB(with filters)
# Load Markdown files

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Adjust levels to project root
base_path = BASE_DIR / "resources" / "data"


# Step1: Traverse through all folders and load documents
def load_documents():
   """Loads and parses the documents from resources folder """

   docs = []

   # Traverse all folders
   for file_path in base_path.rglob("*"):
       department = file_path.parent.name  # engineering/finance/hr/marketing

       if file_path.suffix == ".md":
           loader =  UnstructuredMarkdownLoader(file_path)

       elif file_path.suffix == ".csv":
           loader = CSVLoader(file_path)
       else:
           continue

       loaded_docs = loader.load()

       for doc in loaded_docs:
           docs.append(
               Document(
                   page_content=doc.page_content,
                   metadata={
                       "department": department,
                       "source": file_path.name,
                       "path": str(file_path),
                       "type": file_path.suffix,
                   }
               )
           )

       if not docs:
           raise FileNotFoundError(f"No Markdown files found in {base_path}")

   return docs







