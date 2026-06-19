from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_sql_query_chain
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from app.database.init_db import init_db
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import OperationalError
from typing import Any

from app.rag.get_api_response import get_response
import os
import re
import logging



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# LOAD ENV VARIABLES
load_dotenv()

api_key = os.getenv("API_KEY")

if not api_key:
    raise ValueError("API_KEY missing from environment variables")


model = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
    api_key=api_key,
    timeout=30,
    max_retries=2
)


# RAG tool
@tool
def rag_tool(query: str, config: RunnableConfig) -> str:
    """
    Search all company documents and answer questions.
    Always use thi stool whenever a question may be answered from company documentation.

    Examples:
    - Why did FinSolve choose a microservices architecture?
    - What authentication method does FinSolve use?
    - What is the PTO policy?
    - What are the future platform initiatives?
    - How does the payment service work?
    - What are the onboarding requirements?

    This tool searches architecture documents,
    technical design decisions,
    engineering documentation,
    HR policies,
    internal manuals,
    and company knowledge bases.
    """

    try:
        # Extract user context from runtime config
        configurable = config.get("configurable", {})
        session_id = configurable.get("session_id", "default")
        emp_name = configurable.get("emp_name", "")
        email = configurable.get("email", "")
        departments = configurable.get("departments", [])

        logger.info(f"RAG tool called | session={session_id}")


        # Generate final answer from retrieved context
        response = get_response(
            query=query,
            session_id=session_id,
            emp_name=emp_name,
            email=email,
            departments=departments
        )

        answer_text = response.get("answer", "") if isinstance(response, dict) else response
        return answer_text

    except Exception as e:
        logger.error("RAG TOOL FAILED", exc_info=True)
        return f"RAG system error: {str(e)}"



# DATABASE SETUP
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

    engine = create_engine(f"sqlite:///{db_file_path}", future=True)
    inspector = inspect(engine)
    db_schema = {}

    try:
        for table_name in inspector.get_table_names():
            columns = [col["name"].lower() for col in inspector.get_columns(table_name)]
            db_schema[table_name.lower()] = columns

    except Exception as schema_error:
        logger.warning("Unable to load database schema metadata", exc_info=True)
        db_schema = {}

    table_info = "\n".join(
        [f"{table}: {', '.join(cols)}" for table, cols in db_schema.items()]
    )

except Exception as init_err:
    logger.error("DATABASE INITIALIZATION FAILED", exc_info=True)
    db = None
    db_schema = {}
    table_info = ""


EXECUTIVE_ROLES = {
    "ceo", "chief executive officer", "cfo", "chief financial officer",
    "super admin", "superadmin", "super user", "superuser", "admin", "owner"
}

SENSITIVE_TABLES = {
    "employees", "companies", "departments", "financial_reviews",
    "payroll", "salaries", "payments", "budgets"
}

def normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9_ ]", " ", (text or "").lower())


def has_elevated_access(job_title: str) -> bool:
    if not job_title:
        return False
    normalized = normalize_text(job_title)

    return any(role in normalized for role in EXECUTIVE_ROLES)

def extract_table_name(sql: str) -> list[str]:
    detected = set()
    patterns = [
        r"\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        r"\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        r"\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        r"\bINTO\s+([a-zA-Z_][a-zA-Z0-9_]*)"
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, sql, re.IGNORECASE):
            detected.add(match.group(1).lower())
    return list(detected)


def validate_schema(clean_query: str) -> tuple[bool, str]:
    if not db_schema:
        return True, ""

    referenced_tables = extract_table_name(clean_query)

    for table in referenced_tables:
        if table not in db_schema:
            return False,(
                f"I cannot retrieve that data because the database does not contain a table named '{table}'. "
                "Please ask a different question or use company documents."
            )
    return True, "" # For ceos all access is true


def enforce_rbac(clean_query: str, departments: list[str], job_title: str, email: str) -> tuple[bool, str]:
    if has_elevated_access(job_title):
        return True, ""

    if not departments:
        return False,(
            "You do not have permission to access structured data because your department scope is missing. "
            "Please sign in with an authorized account."
        )

    query_text = normalize_text(clean_query)
    sensitive_tables = extract_table_name(clean_query)

    if any(table in SENSITIVE_TABLES for table in sensitive_tables):
        allowed_values = [normalize_text(dept) for dept in departments if dept]

        if email:
            allowed_values.append(normalize_text(email))

        if not any(value and value in query_text for value in allowed_values):
            return False,(
                "This request appears to need data outside your permitted department scope. "
                "Please ask for information related to your own department or provide a more specific scoped request."
            )

        return True, ""
    return True, ""




# SQL PROMPT
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
            "9. If the User Profile Context is provided in the input, use the actual values (like Name or Email) to filter queries targeting the current user.\n"
            "10. NEVER use placeholder strings like 'current_user' or 'session_user'. Always substitute the literal values from the context into the WHERE clause.\n"
            "11. ONLY use table names that are explicitly listed in the Database Schema section below. Never invent or assume table names like 'leave_policies' exist.\n"
            "12. Employee specific financial records, net income metrics, or leave configurations are contained within the 'employees' or 'companies' tables.\n"

            "Database Schema:\n"
            "{table_info}"
        )
    ),
    ("human", "{input}")
])


# SQL QUERY CHAIN
sql_chain = create_sql_query_chain(
    llm=model,
    db=db,
    prompt=strict_sql_prompt
)


# SQL TOOL
@tool
def sql_tool(query: str, config: RunnableConfig) -> str:
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
        # Extract runtime user context
        configurable = config.get("configurable", {})
        emp_name = configurable.get("emp_name", "")
        email = configurable.get("email", "")
        job_title = configurable.get("job_title", "")
        departments = configurable.get("departments", [])

        enriched_query = (
            "User Profile Context (use these literal values to resolve 'my', 'me', "
            "or the current user - e.g. filter by the user's email or department):\n"
            f"- Name: {emp_name}\n"
            f"- Email: {email}\n"
            f"- Departments: {', '.join(departments) if departments else 'N/A'}\n\n"
            f"User Question: {query}"
        )


        # STEP 1: Generate SQL from LLM
        sql_query = sql_chain.invoke({
            "question": enriched_query,
            "table_info": table_info,
            "top_k": 5
        })

        logger.info(f"Generated SQL: {sql_query}")


        # STEP 2: Clean SQL
        clean_query = (
            sql_query
            .replace("```sql", "")
            .replace("```", "")
            .strip()
        )


        # STEP 3: Validate Query Type
        match = re.search(
            r'\b(SELECT|WITH)\b',
            clean_query,
            re.IGNORECASE
        )

        if not match:
            return "Only SELECT queries are allowed."

        clean_query = clean_query[match.start():]


        # STEP 4: Block Dangerous SQL
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


        # STEP 5: Prevent Multiple Statement
        clean_query = clean_query.strip().rstrip(";")

        if ";" in clean_query:
            return "Multiple SQL statements are not allowed."

        logger.info(f"Executing SQL: {clean_query}")

        # Validate schema and RBAC before execution
        schema_ok, schema_message = validate_schema(clean_query)
        if not schema_ok:
            logger.warning(f"Schema validation failed: {schema_message}")
            return schema_message

        rbac_ok, rbac_message = enforce_rbac(clean_query, departments, job_title, email)
        if not rbac_ok:
            logger.warning(f"RBAC denied SQL execution: {rbac_message}")
            return rbac_message

        logger.info(f"Executing SQL: {clean_query}")

        # Execute Query
        execution_result = db.run(clean_query)

        logger.info("SQL execution successful")

        # STEP 7: Handle Empty Results
        if (
            execution_result is None
            or str(execution_result).strip() in ["", "[]", "()"]
        ):
            return (
                "Database verification: "
                "0 matching records found."
            )

        return str(execution_result)

    except OperationalError as e:
        logger.error("SQL TOOL OPERATIONAL ERROR", exc_info=True)
        return (
            "The requested data could not be retrieved because the database schema or table is unavailable. "
            "Please ask for a different query or use company documents instead."
        )

    except Exception as e:
        logger.error("SQL TOOL FAILED", exc_info=True)

        return (
            "The database query could not be executed. "
            "Please refine your request or ask the assistant to answer from company documents."
        )
