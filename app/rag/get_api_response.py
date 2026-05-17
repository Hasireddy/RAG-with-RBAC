from dotenv import load_dotenv
import os
from typing import List

from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser


from passlib import context
from .create_vector_store import create_vector_store
from .semantic_docs_search import semantic_search


# Load environment variables
load_dotenv()  # reads variables from a .env file and sets them in os.environ
api_key = os.getenv("API_KEY")

client = ChatOpenAI(model="gpt-4.1-mini", temperature=0, api_key=api_key)

# Build vector store once
vector_store = create_vector_store()
memory_store = {}


def get_session_history(session_id):
    if session_id not in memory_store:
        memory_store[session_id] = ChatMessageHistory()

    return memory_store[session_id]


prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a technical documentation expert and an adaptive assistant. 

Analyze the USER QUESTION to determine its intent, then apply the correct logic:

INTENT A: Questions about the chat history, session, or user metadata (e.g., "What queries did I ask?", "What is my name?")
1. Look ONLY at the provided 'history' and USER INFO placeholders.
2. Answer the question directly based on past interactions or metadata.
3. Keep the tone friendly and conversational. Do NOT use the DOCUMENT CONTEXT or say "Information not provided in the documents" for these queries.

INTENT B: Questions about company data, technical details, or specific documents
1. Greet the user by their name if appropriate.
2. EXTRACT QUOTES: Identify and extract relevant quotes from the provided DOCUMENT CONTEXT.
3. VERIFY & FILTER: Use ONLY the provided context. Do not add external knowledge. If the information is missing or irrelevant, strictly reply: "Information not provided in the documents."
4. FORMAT: Summarize the validated answer clearly into one or two sentences using bullet points. Maintain a professional, colleague-to-colleague tone."""),
    MessagesPlaceholder("history"),
    ("human", """USER INFO: 
Name: {emp_name} 
Email: {email} 
Departments: {departments} 

DOCUMENT CONTEXT: 
{context} 

USER QUESTION: 
{query}""")
])

chain = (prompt | client | StrOutputParser() )
chain_with_memory = RunnableWithMessageHistory(chain, get_session_history, input_messages_key="query", history_messages_key="history")


def get_response(query:str, session_id: str, emp_name: str, email: str, departments: List[str]):
    """Returns API response  based on semantic search context"""
    print("******************")
    print(query)
    print(memory_store)
    print(session_id)

    history = get_session_history(session_id)
    print(history.messages)
    context = semantic_search(vector_store, query, departments=departments)

    final_answer = chain_with_memory.invoke({"query": query, "context": context, "emp_name": emp_name, "email": email, "departments": ",".join(departments)},
                                            {"configurable": {"session_id": session_id}})

    data = {
            "answer": final_answer,
            "name": emp_name,
            "email": email,
            "departments": departments,
            "session_id": session_id,
        }

    return data


