import os
import re
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

client = OpenAI(api_key=API_KEY)

SQL_TRIGGERS = [
    "average", "sum", "total", "count", "how many", "top", "trend", "kpi", "revenue",
    "profit", "expense", "salary", "employee", "id", "quarter", "year", "report", "record", "details",
    "list", "filter", "group by", "order by", "where", "select", "show", "what is the", "how many"
]

RAG_TRIGGERS = [
    "policy", "procedure", "guideline", "documentation", "faq", "explain", "what is", "why", "how to",
    "process", "manual", "onboarding", "architecture", "design", "overview", "best practice"
]


def detect_query_type_llm(query: str) -> str:
    normalized = query.strip().lower()

    if not normalized:
        return "RAG"

    for term in SQL_TRIGGERS:
        if re.search(rf"\b{re.escape(term)}\b", normalized):
            return "SQL"

    for term in RAG_TRIGGERS:
        if re.search(rf"\b{re.escape(term)}\b", normalized):
            return "RAG"

    prompt = f"""
    You are a classifier that decides whether  a user's query should be handled by Structured SQL query using SQL (database access) logic or
    unstructured document search(RAG).

   If the query requests specific records, metrics, counts, trends, KPIs, employee data, department data,
    financial figures, or other structured attributes, answer: SQL.

    If the query is conceptual, procedural, policy-oriented, documentation-focused, explanatory, or knowledge-base related,
    answer: RAG.

    Respond with only one word: Either ***SQL*** or ***RAG***.

    Here is the query:
    "{query}"

    Answer:
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]

    )

    # final_response = response.content.strip()
    # return final_response
    result = response.choices[0].message.content.strip().upper()

    if result not in {"SQL", "RAG"}:
        return "RAG"
    return result