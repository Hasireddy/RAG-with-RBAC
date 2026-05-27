from dotenv import load_dotenv
import os
from typing import List

from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langfuse import get_client
from langfuse.langchain import CallbackHandler

from .create_vector_store import create_vector_store
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
vector_store = create_vector_store()
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




prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a technical documentation expert and AI assistant with access to company documents. 
     Your task is to help answer a question using only the provided DOCUMENT CONTEXT. Be concise and accurate. Do not add
     external knowledge. If the information is not provided in the DOCUMENT CONTEXT, say "Information not provided in the documents".
     Ensure you have a friendly tone like you are explaining it to a colleague.
     Summarize the information into one or two sentences.
     #Before answering, Check the user department  {departments} . If the information is related to the user department,
     #provide the response. Otherwise say, "you do not have access to this information".
     #If the information is present in the content and is related to the user department {departments} , provide the information.
     #Else say "Information is not provided in the documents".
     """),

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

chain = (prompt | client | StrOutputParser() )
chain_with_memory = RunnableWithMessageHistory(chain, lambda session_id: memory_store[session_id]["recent_messages"], input_messages_key="query", history_messages_key="history")


def get_response(query:str, session_id: str, emp_name: str, email: str, departments: List[str]):
    """Returns API response  based on semantic search context"""
    print("******************")
    print(query)
    print(memory_store)
    print(session_id)

    session =  get_session_history(session_id)
    history = session["recent_messages"]
    summary = session["summary"]

    print(history.messages)
    context = semantic_search(vector_store, query, departments=departments)

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


