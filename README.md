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
4. Queries are classified and routed accordingly — SQL-type queries are translated to SQL using an LLM and executed on SQLite,
   while RAG-type queries are answered via the retrieval-augmented generation pipeline, and responses are evaluated for quality.

The architecture includes:

* **FastAPI backend**: for business logic, user management, and RAG handling.
* **HTML & CSS**: a clean, interactive chat interface built with HTML and CSS.
* **SQL Agent**: processes structured data queries using an LLM for translation and SQLiteDB for execution.
* **RAG Agent**: retrieves and synthesizes responses from unstructured documents using embeddings and LLMs.
* **RAGAS EVALUATOR**: evaluates responses on metrics like Faithfulness (how grounded the answer 
  is in retrieved context) and Answer Relevancy (how relevant the answer is to the user's question), 
  ensuring trustworthy and high-quality outputs.

# 🚀System Architecture Diagram

<svg width="700" height="600" viewBox="0 0 700 600" xmlns="http://www.w3.org/2000/svg" role="img">
  <title>Query Routing Flowchart — SQL Agent and RAG Agent</title>
  <desc>User queries via Interactive Chatbot and FastAPI Backend are classified and routed to SQL Agent (SQLite) or RAG Agent, with fallback from SQL to RAG on failure.</desc>

  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>

  <rect width="700" height="600" fill="#ffffff"/>

  <!-- === NODE A: User Query === -->
  <rect x="215" y="24" width="270" height="66" rx="10" fill="#fce4fc" stroke="#b060b0" stroke-width="1.5"/>
  <text x="350" y="46" text-anchor="middle" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="#6a1a6a">User Query</text>
  <text x="350" y="63" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="#8a3a8a">Interactive Chatbot</text>
  <text x="350" y="80" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="#8a3a8a">FastAPI Backend</text>

  <!-- A → B -->
  <line x1="350" y1="90" x2="350" y2="132" stroke="#777" stroke-width="1.5" marker-end="url(#arrow)"/>

  <!-- === NODE B: Classifier Diamond === -->
  <polygon points="350,136 490,202 350,268 210,202" fill="#dde0ff" stroke="#4455bb" stroke-width="1.5"/>
  <text x="350" y="197" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#1a2288">Query Classifier Agent</text>
  <text x="350" y="215" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="#2233aa">SQL or RAG?</text>

  <!-- B → C (left, SQL) -->
  <line x1="210" y1="202" x2="110" y2="202" stroke="#777" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="160" y="195" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="#444">SQL</text>

  <!-- B → E (right, RAG) -->
  <line x1="490" y1="202" x2="590" y2="202" stroke="#777" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="540" y="195" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="#444">RAG</text>

  <!-- === NODE C: SQL Agent === -->
  <rect x="10" y="172" width="200" height="60" rx="10" fill="#ccf0cc" stroke="#2a8a2a" stroke-width="1.5"/>
  <text x="110" y="197" text-anchor="middle" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="#1a4a1a">SQL Agent</text>
  <text x="110" y="216" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="#2a622a">NLP → SQL LLM → SQLite</text>

  <!-- === NODE E: RAG Agent === -->
  <rect x="490" y="172" width="200" height="60" rx="10" fill="#b8e2f8" stroke="#1a6899" stroke-width="1.5"/>
  <text x="590" y="197" text-anchor="middle" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="#0a2e5a">RAG Agent</text>
  <text x="590" y="216" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="#1a4a7a">Vector Search + LLM</text>

  <!-- C → F (Success) -->
  <line x1="110" y1="232" x2="110" y2="322" stroke="#777" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="122" y="282" font-family="Arial,sans-serif" font-size="11" fill="#444">Success</text>

  <!-- === NODE F: SQL Response === -->
  <rect x="10" y="322" width="200" height="54" rx="10" fill="#d0f6f6" stroke="#1a8899" stroke-width="1.5"/>
  <text x="110" y="346" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#0a4455">SQL Response to User</text>
  <text x="110" y="363" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="#0e5a66">Structured result returned</text>

  <!-- C → D (Fail — route left then down) -->
  <path d="M 10 202 L -8 202 L -8 456 L 200 456" fill="none" stroke="#cc3333" stroke-width="1.5" stroke-dasharray="6,3" marker-end="url(#arrow)"/>
  <text x="6" y="336" text-anchor="middle" font-family="Arial,sans-serif" font-size="10" fill="#cc3333" transform="rotate(-90,6,336)">Fail or Incomplete</text>

  <!-- === NODE D: Fallback === -->
  <rect x="200" y="429" width="200" height="54" rx="10" fill="#ffe0e0" stroke="#cc3333" stroke-width="1.5"/>
  <text x="300" y="453" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#880000">Fallback Triggered</text>
  <text x="300" y="471" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="#aa1111">SQL failed or incomplete</text>

  <!-- D → E (up-right to RAG Agent) -->
  <path d="M 400 456 L 590 456 L 590 232" fill="none" stroke="#cc3333" stroke-width="1.5" stroke-dasharray="6,3" marker-end="url(#arrow)"/>
  <text x="500" y="449" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="#cc3333">Fallback to RAG</text>

  <!-- E → G -->
  <line x1="590" y1="232" x2="590" y2="322" stroke="#777" stroke-width="1.5" marker-end="url(#arrow)"/>

  <!-- === NODE G: RAG Response === -->
  <rect x="490" y="322" width="200" height="54" rx="10" fill="#d0f6f6" stroke="#1a8899" stroke-width="1.5"/>
  <text x="590" y="343" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#0a4455">RAG Response to User</text>
  <text x="590" y="360" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="#0e5a66">Meaningful contextual answer</text>

  <!-- Legend -->
  <rect x="210" y="528" width="280" height="58" rx="8" fill="#f5f5f5" stroke="#cccccc" stroke-width="1"/>
  <text x="350" y="547" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" font-weight="700" fill="#333">Legend</text>
  <line x1="225" y1="561" x2="263" y2="561" stroke="#777" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="268" y="565" font-family="Arial,sans-serif" font-size="10" fill="#444">Normal flow</text>
  <line x1="225" y1="577" x2="263" y2="577" stroke="#cc3333" stroke-width="1.5" stroke-dasharray="6,3" marker-end="url(#arrow)"/>
  <text x="268" y="581" font-family="Arial,sans-serif" font-size="10" fill="#444">Fallback path (SQL fail → RAG)</text>

</svg>


# Architecture Overview

* Combines structured data querying (SQL) with unstructured document retrieval (RAG).
* Ensures high accuracy and flexibility by selecting the most appropriate engine per query.
* Implements fallback logic for robustness — the user always gets a meaningful response.
* This system is designed to intelligently respond to user queries using either structured SQL or unstructured RAG depending on the nature of the query.

# End-to-End Flow:

### 1. User Interface Layer
A user enters a question through UI.
This query is sent to the FastAPI backend, which handles the core logic.

### 2. Query Classification
The query first reaches a Query Classifier Agent, which analyzes it and decides:
Is this a structured query? (e.g., about data in a table)
Or an unstructured query? (e.g., asking for procedural guidance)

### 3. SQL Agent Path
If the classifier determines it's an SQL-type query:
The query goes to the SQL Agent, which uses an LLM to convert natural language into SQL.
The generated SQL is executed using SQLite, a lightweight embedded database engine.
If the query executes successfully, the result is sent back to the user as a SQL Response.

### 4. Fallback Mechanism
If the SQL query fails or the response is incomplete, a Fallback Trigger is activated.
The system automatically reroutes the query to the RAG Agent.

### 5. RAG Agent Path
The RAG Agent retrieves relevant information from documents using Vector Search (e.g., via FAISS).
The LLM then generates a coherent answer from the retrieved chunks.
The final RAG-based response is sent back to the user.

### 6. Response Evaluation (RAGAS)
Every response generated by the RAG Agent is evaluated using the RAGAS framework across two key metrics:
- **Faithfulness**: measures whether the answer is factually grounded in the retrieved document chunks, 
  reducing hallucinations.
- **Answer Relevancy**: measures how directly and completely the answer addresses the user's original question.
These scores help maintain response quality and build trust in the system over time.

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

### 6. Run the Application

uvicorn app.main:app --reload

Then open your browser and go to:
 http://127.0.0.1:8000






