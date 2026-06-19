from dotenv import load_dotenv
import os
import json
import random
import time
from typing import List, Generator
import logging

from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langfuse import get_client, Langfuse
from langfuse.langchain import CallbackHandler
from concurrent.futures import ThreadPoolExecutor

from .semantic_docs_search import vector_store, semantic_search
from app.rag_evals.ragas_evaluator import evaluate_rag_response
from app.rag_evals.ragas_evaluation_results import log_metrics_to_csv

logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()  # reads variables from a .env file and sets them in os.environ
api_key = os.getenv("API_KEY")

client = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)

# Initialize Langfuse client
langfuse = get_client()

# Initialize Langfuse CallbackHandler for Langchain (tracing)
langfuse_handler = CallbackHandler()

executor = ThreadPoolExecutor(max_workers=1)

# Build vector store once
memory_store = {}
MAX_RECENT_MSGS = 10
EVAL_SAMPLE_RATE = 0.05

#RAGAS_METRIC_NAMES = {"faithfulness", "answer_relevancy", "nv_context_relevance", "nv_response_groundedness"}
RAGAS_METRIC_NAMES = {"faithfulness", "answer_relevancy"}

def clear_session_history(session_id):
    memory_store.pop(session_id, None)

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


summarizer_chain = (summary_prompt | client.bind(max_tokens=500) | StrOutputParser())

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
        Your task is to help answer a user's question using the provided USERINFO, DOCUMENT CONTEXT and tools.
        
        STRICT RULES:
        1. ONLY use information explicitily stated in the USER INFO or the provided DOCUMENT CONTEXT.
        2. DO not assume, extrapolate, or bring in outside knowledge.
        3. If the relevant information is present, summarize it into 1-3 sentences.
        4. The context may contain partial sentences or chunks — still use what is relevant.
        5. Do NOT say "information not provided" if relevant content exists in the context,
            even if it doesn't perfectly match the question phrasing.
        6. Include some emojis like smileys when answering in  a friendly way.
        
        
EXAMPLES:
Input: Hi
Output: Hello👋. Ask me anything?

Input: What are Client applications?
Output: Client applications are Mobile, Web and API applications.

Input: Who invented electricity?
Output:ERROR: Information not provided in the documents.

Input: Why did HR costs increase?
Output: According to the documents, HR costs increased due to expanded employee benefits and wellness programs during the fiscal year.

Input: What is the dress code?
Output: Information not provided in the documents.


"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("system", "Conversation summary: {summary}"),
    MessagesPlaceholder("history"),
    ("human", """


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

chain = (prompt | client.bind(max_tokens=300) | StrOutputParser() )
chain_with_memory = RunnableWithMessageHistory(chain, lambda session_id: memory_store[session_id]["recent_messages"], input_messages_key="query", history_messages_key="history")

def _run_evals(question: str, answer: str, contexts: list[str], trace_id: str, session_id: str, emp_name: str):
    try:
        scores = evaluate_rag_response(
            question=question,
            answer=answer,
            contexts=contexts
        )
        print(scores)
        if scores:
                df = scores.to_pandas()
                log_metrics_to_csv(trace_id, session_id, emp_name, question, df)
                for metric in RAGAS_METRIC_NAMES:
                    if metric not in df.columns:
                        continue
                    value = df[metric][0]
                    if value is not None and value == value:
                        langfuse.create_score(
                            trace_id=trace_id,
                            name=metric,
                            value=float(value),
                            data_type="NUMERIC"
                        )
    except Exception as e:
        logging.error(f"Langfuse scoring failed: {e}")


def get_response(query:str, session_id: str, emp_name: str, email: str, departments: List[str]):
    """Returns API response  based on semantic search context"""
    start_time = time.perf_counter()
    session =  get_session_history(session_id)
    logging.info(f"The user is {emp_name} and the session_id is: {session_id} and session_history: {session}")
    history = session["recent_messages"]

    #if len(history.messages) > MAX_RECENT_MSGS:
        #history.messages = history.messages[-MAX_RECENT_MSGS:]

    summary = session["summary"]

    #generate trace_id so we can reference it for scoring later
    trace_id = Langfuse.create_trace_id()
    langfuse_handler = CallbackHandler()

    t0 = time.perf_counter()
    retrieval = semantic_search(vector_store, query, departments=departments)
    t1 = time.perf_counter()
    logging.info(f"Retrieval: {t1 - t0:.3f}s")

    search_status = retrieval["status"]
    context = retrieval["context"]
    contexts = retrieval["contexts"]

    if search_status == "UNAUTHORIZED":
        return{
            "answer": "You do not have access to this information.",
            "name": emp_name, "email": email, "departments": departments, "session_id": session_id
        }

    if search_status == "NOT_FOUND" or not context:
        return {
            "answer": "Information not provided in the documents."
        }

    logging.info(
        f"History messages: {len(history.messages)}"
    )

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

    t2 = time.perf_counter()
    logging.info(f"LLM Generation: {t2 - t1:.3f}s")

    summarize_old_chat(session_id)

    t3 = time.perf_counter()
    logging.info(f"Summarization: {t3 - t2:.3f}s")

    try:
        if random.random() < EVAL_SAMPLE_RATE:
            logging.info(
                f"Running RAG evaluation for session={session_id}"
            )
            executor.submit(_run_evals, query, final_answer, contexts, trace_id, session_id, emp_name)

        else:
            logging.info(
                f"Skipping RAG evaluation for session={session_id}"
            )

    except Exception as eval_err:
        logging.error(f"Failed to submit background evaluation: {eval_err}")

    end_time = time.perf_counter()
    latency_seconds = end_time - start_time
    print("*********************")
    print(f"Latency: {latency_seconds:.4f} seconds")
    print("*********************")

    data = {
            "answer": final_answer,
            "name": emp_name,
            "email": email,
            "departments": departments,
            "session_id": session_id,
        }

    return data


def stream_response(query: str, session_id: str, emp_name: str, email: str, departments: List[str]) -> Generator[
    str, None, None]:
    """Streams API response chunks based on semantic search context."""
    start_time = time.perf_counter()
    session = get_session_history(session_id)
    logging.info(f"The user is {emp_name}, session_id: {session_id}")

    history = session["recent_messages"]
    summary = session["summary"]

    # Generate trace_id for monitoring
    trace_id = Langfuse.create_trace_id()
    langfuse_handler = CallbackHandler()

    t0 = time.perf_counter()
    retrieval = semantic_search(vector_store, query, departments=departments)
    t1 = time.perf_counter()
    logging.info(f"Retrieval: {t1 - t0:.3f}s")

    search_status = retrieval["status"]
    context = retrieval["context"]
    contexts = retrieval["contexts"]

    # Guard Rails: Return immediate structural responses if blocked or missing
    if search_status == "UNAUTHORIZED":
        yield json.dumps({
            "answer": "You do not have access to this information.",
            "name": emp_name, "email": email, "departments": departments, "session_id": session_id
        })
        return

    if search_status == "NOT_FOUND" or not context:
        yield json.dumps({
            "answer": "Information not provided in the documents."
        })
        return

    logging.info(f"History messages: {len(history.messages)}")

    # Initialize a list to accumulate text chunks as they stream
    full_answer_list = []

    # Stream from LangChain
    stream_iterable = chain_with_memory.stream(
        {
            "summary": summary,
            "query": query,
            "context": context,
            "emp_name": emp_name,
            "email": email,
            "departments": ",".join(departments)
        },
        {
            "configurable": {"session_id": session_id},
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

    # Yield tokens sequentially to the client
    for chunk in stream_iterable:
        # Check if chunk is a string or LangChain ChatGeneration/AIMessageChunk object
        chunk_text = chunk if isinstance(chunk, str) else getattr(chunk, "content", str(chunk))
        full_answer_list.append(chunk_text)

        # Yield metadata or raw token structure depending on client requirements
        yield json.dumps({"token": chunk_text})

    # Reconstruct final complete answer for backend tracking pipelines
    final_answer = "".join(full_answer_list)

    t2 = time.perf_counter()
    logging.info(f"LLM Generation: {t2 - t1:.3f}s")

    # Post-streaming hooks (runs smoothly after user receives all tokens)
    summarize_old_chat(session_id)
    t3 = time.perf_counter()
    logging.info(f"Summarization: {t3 - t2:.3f}s")

    try:
        if random.random() < EVAL_SAMPLE_RATE:
            logging.info(f"Running RAG evaluation for session={session_id}")
            executor.submit(_run_evals, query, final_answer, contexts, trace_id, session_id, emp_name)
        else:
            logging.info(f"Skipping RAG evaluation for session={session_id}")
    except Exception as eval_err:
        logging.error(f"Failed to submit background evaluation: {eval_err}")

    end_time = time.perf_counter()
    latency_seconds = end_time - start_time
    print("*********************")
    print(f"Total stream latency: {latency_seconds:.4f} seconds")
    print("*********************")

    # Yield a final closing payload with complete metadata if needed
    yield json.dumps({
        "status": "completed",
        "name": emp_name,
        "email": email,
        "departments": departments,
        "session_id": session_id,
    })