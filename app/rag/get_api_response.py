from dotenv import load_dotenv
import os

from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from collections import defaultdict

from passlib import context
from .create_vector_store import create_vector_store
from .semantic_docs_search import semantic_search


# Load environment variables
load_dotenv()  # reads variables from a .env file and sets them in os.environ
api_key = os.getenv("API_KEY")

client = ChatOpenAI(model="gpt-4.1-mini", temperature=0, api_key=api_key)

# Build vector store once
vector_store = create_vector_store()
memory_store = defaultdict(list)

# Prompt

def build_prompt_step1(query, context):
    return [
        {"role": "system",
         "content": """You are a technical documentation expert and a helpful assistant for a company.
                        Your task is to help answer a question given in a document. 
                        If the question is about the user (e.g., name, greetings, personal context), always use chat history first. 
                        If the user greets, greet them with their name. 
                        Only use document context for factual/company-related queries.
                        The first step is to extract the relevant quotes from the document. 
                     """
        },
        {"role": "user",
         "content": f"""Question:
{query}

Context:
{context}
"""
        }
    ]


def build_prompt_step2(query, answer1):
    return [
        {"role": "system",
         "content": """You are a technical documentation expert.
                      Given a set of relevant quotes extracted from the document.
                      Please compare the question to the answer.
                      Use only the information provided in the context to answer.
                      Be concise and exact. Do not add external knowledge and hallucinate.
                      If the information is not fully present or not relevant to the provided documents, say "Information not provided in the documents."
                      Ensure the answer is accurate and has a friendly tone like you are explaining it to a colleague.
                     """
        },
        {"role": "user",
         "content": f"""Question:
{query}

Context:
{answer1}
"""
        }
    ]


def build_prompt_step3(query, answer2):
    return [
        {"role": "system",
         "content": """You are a response formatting assistant. 
                        Rewrite the answer clearly and naturally.
                        Summarize the information into one or two sentences.
                        Use Bullet points if multiple items exist.
                        Return Json format if the user requested structured data.
                        Special rules:
                        - If answer contains:
                        "Information not provided in the documents."
                        then return it exactly as-is.

                        Examples:
                        input:"Hi my name is uma"
                        output:"Hello Uma, How can I help you?"

                        input: What are Client applications?
                        output: Client applications are Mobile, Web and API applications.

                        input: What is the financial overview of 2024?
                        output: The financial overview of 2024 is 28%.

                        input: What are Databases?
                        output: Information about Databases is not provided in the documents.

                        input: List employees details?
                        output: {
                          "name": "Krishna Verma",
                          "email": "vihaan.garg@fintechco.com",
                          "location": "Jaipur",
                          "leaves_taken": 21
                        }
                     """
        },
        {"role": "user",
         "content": f"""Question:
{query}

Context:
{answer2}
"""
        }
    ]

"""# Chain
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

)"""

def get_history(session_id: str):
    return memory_store[session_id]


def format_history(history: list):
    """
    Convert memory into readable string for LLM
    """
    return "\n".join(
        [f"User: {m['user']}\nAssistant: {m['assistant']}" for m in history]
    )

def get_response(query:str, session_id: str, emp_name: str, email: str, dept_id: str):
    """Returns API response  based on semantic search context"""
    print(query)
    #context = semantic_search(vector_store, query, department=dept_id)
    context = semantic_search(vector_store, query)
    history = get_history(session_id)
    history_text = format_history(history)

    step1_response  = client.invoke(build_prompt_step1(
        query=f"""
        CHAT HISTORY:
        {history_text}
        QUERY:
        {query}
        """,
        context=context
    ))
    answer1 = step1_response.content

    step2_response = client.invoke(
        build_prompt_step2(query, answer1)
    )
    answer2 = step2_response.content

    # STEP 3: formatting
    step3_response = client.invoke(
        build_prompt_step3(query, answer2)
    )
    final_answer = step3_response.content

    # Store memory
    history.append({
        "user": query,
        "assistant": final_answer
    })

    # optional: limit memory size (prevents token explosion)
    if len(history) > 20:
        history.pop(0)

    data = {
            "answer": final_answer,
            "name": emp_name,
            "email": email,
            "department_id": dept_id,
            "session_id": session_id,
        }

    return data
    """response = chain_with_memory.invoke(
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

    return response.content"""

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