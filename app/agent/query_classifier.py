import os
import re
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

client = OpenAI(api_key=API_KEY)

# Strong, unambiguous signals that a query needs the structured database.
# Generic words ("details", "id", "year", "what is the") were intentionally
# removed because they collide with documentation questions and forced policy
# queries down the SQL path.
SQL_TRIGGERS = [
    "how many", "count", "average", "headcount",
    "salary", "salaries", "leave balance", "leaves balance", "balance leaves",
    "leaves taken", "performance rating", "list all employees", "list employees",
]

# Strong signals that a query is answered from documents / knowledge base.
RAG_TRIGGERS = [
    "policy", "policies", "procedure", "guideline", "documentation", "faq",
    "process", "manual", "onboarding", "architecture", "design", "best practice",
    "pto", "notice period", "handbook", "microservices", "ci/cd", "pull request",
]


def detect_query_type_llm(query: str) -> str:
    normalized = query.strip().lower()

    if not normalized:
        return "RAG"

    sql_hit = any(re.search(rf"\b{re.escape(term)}\b", normalized) for term in SQL_TRIGGERS)
    rag_hit = any(re.search(rf"\b{re.escape(term)}\b", normalized) for term in RAG_TRIGGERS)

    # Only short-circuit when the signal is unambiguous (exactly one category).
    # Anything ambiguous (both or neither) falls through to the LLM classifier.
    if sql_hit and not rag_hit:
        return "SQL"
    if rag_hit and not sql_hit:
        return "RAG"

    prompt = f"""
    You are a classifier that decides whether  a user's query should be handled by:
    - Structured SQL query using SQL (database access) logic or
    - unstructured document search(RAG).

   RULES:
   - If the query requests specific records, metrics, counts, trends, KPIs, employee data, department data,
    financial figures, or other structured attributes, answer: SQL.

    - If the query is conceptual, procedural, policy-oriented, documentation-focused, explanatory, or knowledge-base related,
    answer: RAG.

    Response format:
    - Respond with only one word: Either SQL or RAG.
    - Do not include any explanation or additional text.

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


