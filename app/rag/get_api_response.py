from dotenv import load_dotenv
import os
from typing import List

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

        new_summary = summarizer_chain.invoke({"conversation": combined})
        memory_store[session_id]["summary"]= new_summary
        memory_store[session_id]["recent_messages"].messages = recent_msgs[-MAX_RECENT_MSGS:]




prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a technical documentation expert and AI assistant with access to company documents. 

Analyze the USER QUESTION to determine its intent, then apply the correct logic:

INTENT A: Questions about the chat history, session, or user metadata (e.g., "What queries did I ask?", "What is my name?")
1. Look ONLY at the provided 'history' and USER INFO placeholders.
2. Answer the question directly based on past interactions or metadata.
3. Keep the tone friendly and conversational.
. Do NOT use the DOCUMENT CONTEXT or say "Information not provided in the documents" for these queries.

INTENT B: Questions about company data, technical details, or specific documents
#1. Greet the user by their name if appropriate.
2. EXTRACT QUOTES: Identify and extract relevant quotes from the provided DOCUMENT CONTEXT.
3. VERIFY & FILTER: Use ONLY the provided context. Do not add external knowledge. Ensure the answer is accurate.
If the information is missing or irrelevant, strictly reply: "Information not provided in the documents."
Before answering , check the "Document Metadata" below. If the document's department does not match with the user's department,
Departments: {departments} you must strictly reply: "You do not have access to these documents."
4. FORMAT: Summarize the validated answer clearly into one or two sentences using bullet points. Maintain a professional, colleague-to-colleague tone.

 Examples:
                        input:"Hi my name is uma"
                        output:"Hello Uma, How can I help you?"

                        input: What are Client applications?
                        output: Client applications are Mobile, Web and API applications.

                        input: What is the financial overview of 2024?
                        output: You do not gave access to these documents.

                        input: What are Databases?
                        output: Information about Databases is not provided in the documents."""),


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

### INSTRUCTIONS
1. Check the security rule first.
2. If authorized, answer the question using only the provided context.
3. If unauthorized, trigger the exact security response.""")
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

    final_answer = chain_with_memory.invoke({"summary": summary, "query": query, "context": context, "emp_name": emp_name, "email": email, "departments": ",".join(departments)},
                                            {"configurable": {"session_id": session_id}})

    summarize_old_chat(session_id)

    data = {
            "answer": final_answer,
            "name": emp_name,
            "email": email,
            "departments": departments,
            "session_id": session_id,
        }

    return data


