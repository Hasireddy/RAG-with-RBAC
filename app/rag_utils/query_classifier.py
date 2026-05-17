from openai import OpenAI
from dotenv import load_dotenv
import os


# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

client = OpenAI(api_key=API_KEY)



def detect_query_type_llm(query:str) -> str:
    query = query.lower()

    prompt = f"""
    You are a classifier that decides if a user's query should be handled by Structured SQL query logic or
    unstructured document search(RAG).
    
    If the query contains terms related to ***structured analysis(e.g., "average", "sum", "total", "count", "how many",
    "filter", "greater than", "less than", "top-5", "grou by", "details of employee", "list employees" etc),
    classify it as -> "SQL".
    
    If the query is more about summarization, definitions, general understanding, or cannot be answered by structured tabular
    data, classify it as -> "RAG".
    
    Respond with only one word: Either ***SQL*** or ***RAG***.
    
    Here is the query:
    "{query}"
    
    Answer:
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0,
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]

    )

    #final_response = response.content.strip()
    #return final_response
    return response.choices[0].message.content.strip()


