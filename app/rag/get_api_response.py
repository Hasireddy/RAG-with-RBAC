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

    Rules:
    - Use chat history for greetings, names, and conversational context.
    - Use document context only for company/document-related answers.
    - Answer only from the provided context.
    - Do not hallucinate.
    - If information is unavailable, say:
      "Information not provided in the documents."

    Formatting:
    - Keep answers concise.
    - Use bullet points if needed.
    - Return JSON only if the user explicitly asks for structured output.
    """
        ),

        MessagesPlaceholder(variable_name="history"),

        (
            "human",
            """
    Question:
    {query}

    Document Context:
    {context}
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


def get_response(query:str, session_id: str):
    """Returns API response  based on semantic search context"""
    print(query)
    #context = semantic_search(vector_store, query, department=dept_id)
    context = semantic_search(vector_store, query)

    # Invoke chain
    response = chain_with_memory.invoke(
        {
            "query": query,
            "context": context
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