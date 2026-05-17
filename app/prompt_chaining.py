from dotenv import load_dotenv
import os

from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from .create_vector_store import create_vector_store
from .semantic_docs_search import semantic_search

# Load environment variables
load_dotenv()  # reads variables from a .env file and sets them in os.environ
api_key = os.getenv("API_KEY")

client = ChatOpenAI(model="gpt-4.1-mini", temperature=0, api_key=api_key)

# Build vector store once
vector_store = create_vector_store()


def get_response(query: str):
    """Returns API response  based on semantic search context"""
    print(query)
    # context = semantic_search(vector_store, query, department=dept_id)
    context = semantic_search(vector_store, query)

    # User prompt
    prompt_step1 = [
        {"role": "system",
         "content": f"""You are a technical documentation expert and a helpful assistant for a company.
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

    step1_response = client.invoke(prompt_step1)
    answer1 = step1_response.content
    print(f"step1:{answer1}")

    prompt_step2 = [
        {"role": "system",
         "content": f"""
                      You are a technical documentation expert.
                      Given a set of relevant quotes extracted from the document.
                       Please compare the question to the answer.
                       Use only the information provided in the context to answer.
                       Be concise and exact. Do not add external knowledge and hallucinate.
                       If the information is not fully present or not relevant to the provided documents, say "Information not provided in the documents."
                       Ensure the answer is the accurate, has a friendly tone like you are explaining it to a colleague.
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

    answer2 = client.invoke(prompt_step2)
    print(f"step2:{answer2.content}")

    prompt_step3 = [
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

                        Here are few examples of the input and output .
                        input:"Hi my name is uma"
                        output:"Hello Uma, How can I help you?
                        input: What are Client applications?
                        output: Client applications are Mobile, Web and API applications.
                        input: What is the financial overview of 2024?
                        output: The financial overview of 2024 is 28%.
                        input: What are Databases?
                        output: Information about Databases is not provided in the documents.
                        "input": List the full name, email id and location of employees in the sales department who took more than 10 leaves?
                        "output": 
                                    {  "name": "Krishna Verma",
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

    answer3 = client.invoke(prompt_step3)
    print(f"step3:{answer3.content}")

    # generate answer
    response = answer3.content

    print(response)
    return response




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



def get_response(query:str, session_id: str, emp_name: str, email: str, departments: List[str]):
    """Returns API response  based on semantic search context"""
    print(query)
    context = semantic_search(vector_store, query, departments=departments)
    #context = semantic_search(vector_store, query)

    """step1_response  = client.invoke(build_prompt_step1(
        query=f"""
        """QUERY:
        {query}"""
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
    final_answer = step3_response.content"""
    final_answer = chain_with_memory.invoke({"query": query, "context": context})

    data = {
            "answer": final_answer,
            "name": emp_name,
            "email": email,
            "departments": departments,
            "session_id": session_id,
        }

    return data

Your task is to answer the user's question using the provided document context.
#2. CHECK USER CONTEXT: If the question is about the user (e.g., name, greetings, personal context), prioritize chat history or user metadata. Greet them by name if known.
#3. EXTRACT QUOTES: Identify and extract the relevant quotes from the provided document context.
#4. VERIFY & FILTER: Compare the question to the extracted text. Use ONLY the provided context. Do not add external knowledge or hallucinate. If the information is missing or irrelevant, strictly reply: "Information not provided in the documents."
#5. FORMAT THE OUTPUT: Rewrite the validated answer clearly and naturally. Summarize the information into one or two sentences using bullet points.