from dotenv import load_dotenv
import os
import re
from typing import List

from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import create_react_agent, AgentExecutor
from langfuse import get_client
from langfuse.langchain import CallbackHandler


from .semantic_docs_search import semantic_search



# Load environment variables
load_dotenv()  # reads variables from a .env file and sets them in os.environ
api_key = os.getenv("API_KEY")

client = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, api_key=api_key)

# Initialize Langfuse client
langfuse = get_client()

# Initialize Langfuse CallbackHandler for Langchain (tracing)
langfuse_handler = CallbackHandler()

# Build vector store once
#vector_store = create_vector_store()
memory_store = {}
MAX_RECENT_MSGS = 10


def get_session_history(session_id):
    if session_id not in memory_store:
        memory_store[session_id] = {"summary": "", "recent_messages": ChatMessageHistory()}

    return memory_store[session_id]


summary_prompt = ChatPromptTemplate.from_messages([
    ("system",  """You are an expert research assistant. Your task is to create a concise, high-density summary of the provided text.

Strict Rules:
1. Rely ONLY on the clear facts directly mentioned in the context.
2. Do not assume, extrapolate, or bring in outside knowledge.
3. Any facts or extrapolation not directly mentioned must be considered completely untruthful.
4. Maintain a neutral, factual tone without repeating conversational filler.

Format your output exactly as follows:
- **One-Sentence Overview**: A single sentence capturing the main thesis or primary event.
- **Key Takeaways**: A bulleted list of 3 to 5 distinct, high-impact facts or core points.
"""),

("human", "{conversation}")
])


summarizer_chain = (summary_prompt | client | StrOutputParser())

def summarize_old_chat(session_id):
    session = memory_store[session_id]
    recent_msgs = session["recent_messages"].messages
    previous_summary = session["summary"]


    if len(recent_msgs) > MAX_RECENT_MSGS:
        old_msgs = recent_msgs[:-MAX_RECENT_MSGS]
        conversation = "\n".join([f"{message.type}: {message.content}" for message in old_msgs])
        combined = f"""
        PREVIOUS_SUMMARY: {previous_summary}
        NEW_CONVERSATION: {conversation}
        """

        new_summary = summarizer_chain.invoke({"conversation": combined}, config={
            "callbacks": [langfuse_handler],
            "run_name": "conversation_summary"
        })
        memory_store[session_id]["summary"]= new_summary
        memory_store[session_id]["recent_messages"].messages = recent_msgs[-MAX_RECENT_MSGS:]


system_prompt = f"""You are technical documentation expert and AI assistant for a company.
        Your task is to help answer a user's question from the provided DOCUMENT CONTEXT and tools.
        
        You have access to the following tools:
            - rag_tool: for company documents
            - sql_tool: for structured database queries

STRICT RULES (never violate these):
1. ONLY use information explicitly stated in the DOCUMENT CONTEXT or the information from the tools.
2. If the DOCUMENT CONTEXT does not contain an answer, respond EXACTLY with:
   "I'm sorry, I can only answer questions related to company documents and tools."
3. If the information is present, summarize it to 2 or 3 sentences.



EXAMPLES:
Input: What are Client applications?
Output: Client applications are Mobile, Web and API applications.

Input: What are Unicorns?
Output: I'm sorry, information about Unicorns is not provided in the company documents.

Input: Who invented electricity?
Output: I can only assist with company-related questions.

Input: Why did HR costs increase?
Output: According to the documents, HR costs increased due to expanded employee benefits and wellness programs during the fiscal year.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("system", "Conversation summary: {summary}"),
    MessagesPlaceholder("history"),
    ("human", """USER INFO: 
Name: {emp_name} 
Email: {email} 
Departments: {departments} 

DOCUMENT CONTEXT: 
{context} 

USER QUESTION: 
{query}
.""")
])


OFF_TOPIC_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a query classifier. Decide if the user's question is relevant to a company internal assistant.
A question is RELEVANT if it could be about: company policies, employees, internal tools, products, databases, or operations.
A question is IRRELEVANT if it is about: general knowledge, history, science, coding tutorials, entertainment, etc.

Respond with ONLY one word: RELEVANT or IRRELEVANT."""),
    ("human", "{query}")
])

guard_chain = (OFF_TOPIC_PROMPT | client | StrOutputParser())

def is_query_relevant(query: str) -> bool:
    result = guard_chain.invoke({"query": query})
    return result.strip().upper() == "RELEVANT"
chain = (prompt | client | StrOutputParser() )
chain_with_memory = RunnableWithMessageHistory(chain, lambda session_id: memory_store[session_id]["recent_messages"], input_messages_key="query", history_messages_key="history")


def get_response(query:str, session_id: str, emp_name: str, email: str, departments: List[str]):
    """Returns API response  based on semantic search context"""
    print("******************")
    print(query)
    print(memory_store)
    print(session_id)
    relevant = is_query_relevant(query)
    print(f"[GUARD] Query: '{query}' → Relevant: {relevant}")

    if not relevant:
        return {"answer": "I can only assist with company-related questions."}
    # 🔒 Guard: reject off-topic queries early

    session =  get_session_history(session_id)
    history = session["recent_messages"]
    summary = session["summary"]

    print(history.messages)
    context = semantic_search(vector_store, query, departments=departments)

    if not context:
        return {
            "answer": "I could not find any relevant information in the documents for your query."
        }

    final_answer = chain_with_memory.invoke(
        {
                 "summary": summary,
                 "query": query,
                 "context": context,
                 "emp_name": emp_name,
                 "email": email,
                 "departments": ",".join(departments)
              },

      {
              "configurable": {
                  "session_id": session_id
                },
                "callbacks": [langfuse_handler],
                "metadata": {
                    "user_email": email,
                    "session_id": session_id,
                    "employee_name": emp_name,
                    "departments": departments
                },
                "run_name": "rag-rbac",
            }
    )

    summarize_old_chat(session_id)

    data = {
            "answer": final_answer,
            "name": emp_name,
            "email": email,
            "departments": departments,
            "session_id": session_id,
        }

    return data


