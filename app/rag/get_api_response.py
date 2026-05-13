from dotenv import load_dotenv
import os

from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser


from .create_vector_store import create_vector_store
from .semantic_docs_search import semantic_search


# Load environment variables
load_dotenv()  # reads variables from a .env file and sets them in os.environ
api_key = os.getenv("API_KEY")

client = ChatOpenAI(model="gpt-4.1-mini", temperature=0, api_key=api_key)

# Build vector store once
vector_store = create_vector_store()

# prompt
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are a technical documentation expert and helpful assistant.

You have access to three sources of information:

---

1. USER CONTEXT (personal information about the logged-in user):
- Name: {emp_name}
- Email: {email}
- Department ID: {dept_id}

RULES FOR USER CONTEXT:
Always use this for identity-related questions such as:
- If the question asks about the user (name, email, identity), answer ONLY from this section.
- Never say "information not provided" if emp_name exists.
- Always greet the user using emp_name when starting conversation like:
"Hello {emp_name}"

---

2. CHAT HISTORY:
You may use previous conversation context to maintain continuity and understand references.

---

3. DOCUMENT CONTEXT (company knowledge base):
{context}

Use DOCUMENT CONTEXT ONLY for company, technical, or documentation-related questions.

---

RULES:
- Never mix user context with document context.
- If the answer is not found in either USER CONTEXT or DOCUMENT CONTEXT, say:
  "Information not provided in the documents."
- Do not hallucinate or assume missing information.
- Be concise and professional.
- Use bullet points if needed.
- Return JSON only if explicitly requested.
"""
    ),

    MessagesPlaceholder(variable_name="history"),

    (
        "human",
        """
Question:
{query}
"""
    )
])

# Chain
chain = prompt | client
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

chain_with_memory = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="query",
    history_messages_key="history"

)


def get_response(query:str, session_id: str, emp_name: str, email: str, dept_id: str):
    """Returns API response  based on semantic search context"""
    print(query)
    #context = semantic_search(vector_store, query, department=dept_id)
    context = semantic_search(vector_store, query)

    # Invoke chain
    response = chain_with_memory.invoke(
        {
            "query": query,
            "context": context,
            "emp_name": emp_name,
            "email": email,
            "dept_id": dept_id
        },
        config={
            "configurable": {
                "session_id": session_id
            }
        }
    )

    return response.content

"""while True:
    user_input = input("user: ")
    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    response = chain_with_memory.invoke(
        {"query": user_input},
        config={"configurable": {"session_id": "user1"}}
    )
    print(response.content)

#print(store)"""