from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_sql_query_chain
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from app.database.init_db import init_db

from app.rag.get_api_response import get_response
from app.rag.semantic_docs_search import vector_store, semantic_search

import os
import re
import logging
import traceback

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================================================
# LOAD ENV VARIABLES
# =========================================================

load_dotenv()

api_key = os.getenv("API_KEY")

if not api_key:
    raise ValueError("API_KEY missing from environment variables")

# =========================================================
# LLM MODEL
# =========================================================

model = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
    api_key=api_key,
    timeout=30,
    max_retries=2
)

# =========================================================
# RAG TOOL
# =========================================================

@tool
def rag_tool(query: str, config: RunnableConfig) -> str:
    """
    Search enterprise company documents and answer questions.

    Use for:
    - Policies
    - Documentation
    - Employee knowledge
    - Unstructured company information
    """

    try:
        # Extract user context from runtime config
        configurable = config.get("configurable", {})

        session_id = configurable.get("session_id", "default")
        emp_name = configurable.get("emp_name", "")
        email = configurable.get("email", "")
        departments = configurable.get("departments", [])

        logger.info(f"RAG tool called | session={session_id}")

        # Semantic retrieval with RBAC filtering
        context = semantic_search(
            vector_store=vector_store,
            query=query,
            departments=departments,
            k=5
        )

        if not context:
            return "No relevant information found in company documents."

        # Generate final answer from retrieved context
        response = get_response(
            query=query,
            context=context,
            emp_name=emp_name
        )

        return response

    except Exception as e:
        logger.error("RAG TOOL FAILED", exc_info=True)
        return f"RAG system error: {str(e)}"

# =========================================================
# DATABASE SETUP
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

db_file_path = os.path.join(BASE_DIR, "company_database.db")

logger.info(f"Database path: {db_file_path}")
if not os.path.exists(db_file_path):
    logger.warning(f"Database file missing at {db_file_path}. Creating an empty database file...")
    # Touch the file path to create an empty document container on disk
    with open(db_file_path, "w") as f:
        pass

try:
    #init_db()
    db = SQLDatabase.from_uri(f"sqlite:///{db_file_path}")

    logger.info(
        f"Loaded DB tables: {db.get_usable_table_names()}"
    )

except Exception as init_err:
    logger.error("DATABASE INITIALIZATION FAILED", exc_info=True)
    db = None

# =========================================================
# SQL PROMPT
# =========================================================

strict_sql_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        (
            "You are a SQLite expert.\n"
            "Generate a syntactically correct SQLite SELECT query.\n\n"

            "CRITICAL RULES:\n"

            "1. ONLY generate SELECT queries.\n"

            "2. NEVER generate INSERT, UPDATE, DELETE, "
            "DROP, ALTER, CREATE, or TRUNCATE statements.\n"

            "3. Always use case-insensitive matching.\n"

            "4. Use LOWER(column_name) when appropriate.\n"

            "5. Limit results to top {top_k} rows unless specified.\n"

            "6. ONLY output raw executable SQL.\n"

            "7. Do NOT use markdown formatting.\n"

            "8. Do NOT explain the query.\n\n"

            "Database Schema:\n"
            "{table_info}"
        )
    ),
    ("human", "{input}")
])

# =========================================================
# SQL QUERY CHAIN
# =========================================================

sql_chain = create_sql_query_chain(
    llm=model,
    db=db,
    prompt=strict_sql_prompt
)

# =========================================================
# SQL TOOL
# =========================================================

@tool
def sql_tool(query: str) -> str:
    """
    Query structured SQLite database.

    Use for:
    - Counts
    - Aggregations
    - Analytics
    - Filtering
    - Structured/tabular data
    """

    if db is None:
        return "Database system unavailable."

    try:

        # =================================================
        # STEP 1: Generate SQL from LLM
        # =================================================

        sql_query = sql_chain.invoke({
            "question": query
        })

        logger.info(f"Generated SQL: {sql_query}")

        # =================================================
        # STEP 2: Clean SQL
        # =================================================

        clean_query = (
            sql_query
            .replace("```sql", "")
            .replace("```", "")
            .strip()
        )

        # =================================================
        # STEP 3: Validate Query Type
        # =================================================

        match = re.search(
            r'\b(SELECT|WITH)\b',
            clean_query,
            re.IGNORECASE
        )

        if not match:
            return "Only SELECT queries are allowed."

        clean_query = clean_query[match.start():]

        # =================================================
        # STEP 4: Block Dangerous SQL
        # =================================================

        forbidden = [
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "ALTER",
            "TRUNCATE",
            "CREATE",
            "ATTACH",
            "PRAGMA"
        ]

        upper_query = clean_query.upper()

        if any(word in upper_query for word in forbidden):
            return "Unsafe SQL operation detected."

        # =================================================
        # STEP 5: Prevent Multiple Statements
        # =================================================

        clean_query = clean_query.strip().rstrip(";")

        if ";" in clean_query:
            return "Multiple SQL statements are not allowed."

        logger.info(f"Executing SQL: {clean_query}")

        # =================================================
        # STEP 6: Execute Query
        # =================================================

        execution_result = db.run(clean_query)

        logger.info("SQL execution successful")

        # =================================================
        # STEP 7: Handle Empty Results
        # =================================================

        if (
            execution_result is None
            or str(execution_result).strip() in ["", "[]", "()"]
        ):
            return (
                "Database verification: "
                "0 matching records found."
            )

        # =================================================
        # STEP 8: Return Result
        # =================================================

        return str(execution_result)

    except Exception as e:
        logger.error("SQL TOOL FAILED", exc_info=True)

        return (
            "Database query failed. "
            f"Technical details: {str(e)}"
        )
