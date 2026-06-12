# 🤖 FinSolve Role-Based Chatbot - AI document assistant - A Role Based Access Control System

FinSolve is a secure, intelligent chatbot powered by LLMs + RAG with Role Based Access Control(RBAC) that answers questions from enterprise documents
and ensures employees access only the information aligned with their corporate privileges.

# 🧩 Business Problem

1. FinSolve Technologies faced operational inefficiencies caused by communication delays and fragmented document access across departments like Finance, Marketing, Engineering , and C-level Executives.
2. Departmental isolation limited timely access to relevant information, slowing decision-making, strategic planning, and project execution.
3. The organization required a secure, role-based AI solution to deliver on-demand, department-specific insights while enforcing strict access controls to maintain data confidentiality and operational efficiency.


# 🧠 Solution Overview

1. To address this issue, an internal AI chatbot was developed using Retrieval Augmented Generation (RAG) and Role-Based Access Control (RBAC).
2. It ensures that every user receives accurate, secure, and role-relevant information instantly.
3. Users can upload documents (Markdown, CSV), and the system retrieves answers based on the user's role.
4. Queries are classified and routed accordingly — SQL-type queries are translated to SQL using an LLM and executed on SQLiteDB,
   while RAG-type queries are answered via the retrieval-augmented generation pipeline, and responses are evaluated for quality.

The architecture includes:

* **FastAPI backend**: for business logic, user management, and RAG handling.
* **HTML & CSS **: for interactive Chat Interface
* **SQL Agent**: processes structured data queries using an LLM for translation and SQLiteDB for execution.
* **RAG Agent**: retrieves and synthesizes responses from unstructured documents using embeddings and LLMs.
* **RAGAS EVALUATOR**: to ensure better user trust in responses

# 🚀System Architecture Diagram




# Quick Start
### 1. Clone the Repository

https://github.com/Hasireddy/RAG-with-RBAC.git

cd RAG-with-RBAC

### 2. Set Virtual environment

python -m venv myenv

### 3. Activate Virtual environment

myenv/Scripts/activate

### 4. Install Dependencies

pip install -r requirements.txt

### 5. Add your API Keys
Make sure to set your OPENAI_API_KEY in .env file.

### 4. Run the Application

uvicorn app.main:app --reload

Then open your browser and go to:
 http://127.0.0.1:8000






