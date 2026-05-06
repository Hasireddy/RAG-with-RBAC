from dotenv import load_dotenv
from pathlib import Path
import os

from langchain_openai import ChatOpenAI

from .create_vector_store import create_vector_store
from .semantic_docs_search import semantic_search

# Load environment variables
load_dotenv()  # reads variables from a .env file and sets them in os.environ
api_key = os.getenv("API_KEY")

client = ChatOpenAI(model="gpt-4.1-mini", temperature=0, api_key=api_key)

# Build vector store once
vector_store = create_vector_store()


def get_response(query:str):
    """Returns API response  based on semantic search context"""
    print(query)
    context = semantic_search(vector_store, query)

    # User prompt
    prompt_step1 = [
        {"role": "system",
         "content": """You are a technical documentation expert and a helpful assistant for a company.
                        Your task is to help answer a question given in a document.    
                        The first step is to extract the relevant quotes from the document."""
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
         "content": """
                      Given a set of relevant quotes extracted from the document.
                       Please compare the question to the answer.
                       Use only the information provided in the context to answer.
                       Be concise and exact. Do not add external knowledge and hallucinate.
                       If the information is not fully present, say "Information not provided in the documents.
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
         "content": """Summarize the information into one or two sentences.
                        Use Bullet points if appropriate.
                        Use Json format if required.
                        Here are few examples of the input and output .
                        input:"Hi"
                        output:"Hello, How can I help you?
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
    response = answer3

    print(response.content)
    return response.content


# Example usage
#query = "What is Python?"
#query="List all employees details in sales department who took more then 10 leaves?"
#query="Explain employee onboarding benefits?"
query="Explain Public Holidays Policy?"
#print("API Response:", get_response(query))