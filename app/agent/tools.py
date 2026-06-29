from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from app.database.init_db import init_db
from sqlalchemy import create_engine, inspect, text
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

    # Only expose business-relevant tables to the text-to-SQL model. Internal
    # bookkeeping tables (chat_messages, responses) are deliberately omitted so
    # the model never tries to query them (least-privilege / data minimization).
    RELEVANT_TABLES = ["employees", "departments", "companies"]
    table_info_lines = [
        f"{table}: {', '.join(db_schema[table])}"
        for table in RELEVANT_TABLES
        if table in db_schema
    ]
    table_info = "\n".join(table_info_lines)

    if table_info:
        # Curated relationship / semantic notes greatly improve SQL correctness.
        table_info += (
            "\n\nRelationships & column notes:\n"
            "- employees.dept_id is a JSON ARRAY of department ids (each id -> departments.id).\n"
            "- employees.company_id references companies.id.\n"
            "- departments.id is the value stored inside employees.dept_id.\n"
            "- leaves_balance = leave days REMAINING; leaves_taken = leave days ALREADY USED.\n"
            "- Do NOT confuse leaves_balance with leaves_taken.\n"
        )

    # Known department names (lowercased) -> id. Used to detect when a user
    # explicitly asks about a department other than their own.
    DEPARTMENT_NAME_TO_ID = {}
    try:
        with engine.connect() as conn:
            for row in conn.execute(text("SELECT id, dept_name FROM departments")):
                if row[1]:
                    DEPARTMENT_NAME_TO_ID[str(row[1]).strip().lower()] = int(row[0])
    except Exception:
        logger.warning("Unable to load department names for scope guard", exc_info=True)
        DEPARTMENT_NAME_TO_ID = {}

except Exception as init_err:
    logger.error("DATABASE INITIALIZATION FAILED", exc_info=True)
    db = None
    db_schema = {}
    table_info = ""
    DEPARTMENT_NAME_TO_ID = {}


# Job titles granted unrestricted structured-data access. Kept intentionally
# narrow (whole-word, exact executive titles) to honour least-privilege; generic
# substrings like "admin" are excluded so they cannot silently elevate access.
EXECUTIVE_ROLES = {
    "ceo", "chief executive officer",
    "cfo", "chief financial officer",
    "coo", "chief operating officer",
    "cto", "chief technology officer",
}

# Tables holding personal employee data: every query must be department-scoped.
PERSONAL_TABLES = {"employees"}

# Internal/operational tables that must never be surfaced through the chat tool.
BLOCKED_TABLES = {"chat_messages", "responses"}

# Secret columns that must never be returned to anyone, under any circumstance.
BLOCKED_COLUMNS = {"hashed_password", "password"}

# Personal-sensitive columns: only the requesting user's OWN record may expose
# these. They are withheld for colleagues even within the same department.
SELF_ONLY_COLUMNS = {"salary", "performance_rating", "leaves_balance", "leaves_taken"}


def normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9_ ]", " ", (text or "").lower())


def has_elevated_access(job_title: str) -> bool:
    """True only for exact, whole-word executive titles (e.g. CEO, CFO)."""
    if not job_title:
        return False
    tokens = set(normalize_text(job_title).split())
    for role in EXECUTIVE_ROLES:
        role_tokens = role.split()
        if all(tok in tokens for tok in role_tokens):
            return True
    return False


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
        # json_each / json_tree are SQLite table-valued functions, not real
        # tables, and are legitimately used to filter the dept_id JSON array.
        if table in {"json_each", "json_tree"}:
            continue
        if table not in db_schema:
            return False,(
                f"I cannot retrieve that data because the database does not contain a table named '{table}'. "
                "Please ask a different question or use company documents."
            )
    return True, ""


def _allowed_dept_id_set(dept_ids) -> set[int]:
    """The numeric department ids the current user is permitted to access."""
    allowed = set()
    for did in (dept_ids or []):
        text = str(did).strip()
        if text.isdigit():
            allowed.add(int(text))
    return allowed


def _extract_dept_scope_ids(lower_query: str) -> set[int]:
    """
    Department ids that the query restricts employees.dept_id membership to.

    Recognises the JSON-membership scoping clause across the equivalent forms
    the model may emit, e.g.:
        EXISTS (SELECT 1 FROM json_each(employees.dept_id) WHERE value IN (3))
        EXISTS (SELECT 1 FROM json_each(employees.dept_id) WHERE value = 3)
        3 IN (SELECT value FROM json_each(employees.dept_id))
        json_each.value = 3
    """
    ids = set()
    # ... WHERE value = N   /   WHERE json_each.value = N
    for match in re.finditer(r"value\s*=\s*(\d+)", lower_query):
        ids.add(int(match.group(1)))
    # ... WHERE value IN (a, b, ...)
    for match in re.finditer(r"value\s+in\s*\(([^)]*)\)", lower_query):
        ids.update(int(num) for num in re.findall(r"\d+", match.group(1)))
    # ... N IN (SELECT value FROM json_each(...dept_id...))
    for match in re.finditer(
        r"(\d+)\s+in\s*\(\s*select\s+value\s+from\s+json_each", lower_query
    ):
        ids.add(int(match.group(1)))
    return ids


def _has_dept_scope_construct(lower_query: str) -> bool:
    """True if the query references a json_each membership over dept_id."""
    return bool(re.search(r"json_each\s*\(\s*[a-z_.]*dept_id", lower_query))


def enforce_rbac(
    clean_query: str,
    departments: list[str],
    job_title: str,
    email: str,
    dept_ids: list[str] | None = None,
) -> tuple[bool, str]:
    """
    Deterministic, defence-in-depth authorization for generated SQL.

    Enforces three independent rules for non-executive users:
      1. Internal tables and secret columns are never readable.
      2. Personal-sensitive columns (salary, ratings, leaves) are readable only
         for the requesting user's own record.
      3. Any query against the employees table must be scoped to the user's own
         department id(s); cross-department access is rejected.
    """
    # Executives (CEO/CFO/COO/CTO) bypass row/column scoping.
    if has_elevated_access(job_title):
        return True, ""

    lower_query = clean_query.lower()
    query_text = normalize_text(clean_query)
    referenced_tables = extract_table_name(clean_query)

    # Rule 1a: internal/operational tables are off-limits.
    if any(table in BLOCKED_TABLES for table in referenced_tables):
        logger.warning(f"RBAC: blocked internal table access | tables={referenced_tables}")
        return False, (
            "That information isn't available through this assistant. "
            "Please ask about company documents or your own department's data."
        )

    # Rule 1b: secret columns are never returned.
    if any(re.search(rf"\b{re.escape(col)}\b", lower_query) for col in BLOCKED_COLUMNS):
        logger.warning("RBAC: blocked credential column access")
        return False, "For security reasons, credential information cannot be retrieved."

    touches_personal = any(table in PERSONAL_TABLES for table in referenced_tables)
    if not touches_personal:
        # Non-personal reference tables (companies, departments) are allowed.
        return True, ""

    # ----- The query reads the employees table from here on. -----
    if not (departments or dept_ids):
        return False, (
            "You do not have permission to access employee data because your department "
            "scope is missing. Please sign in with an authorized account."
        )

    # `SELECT *` would implicitly expose secret/sensitive columns; require
    # explicit, reviewable column selection instead.
    if re.search(r"select\s+\*", lower_query) or re.search(r"\bemployees\s*\.\s*\*", lower_query):
        return False, (
            "Please ask for specific employee fields (for example name, email, or job title) "
            "rather than all fields."
        )

    # Is the query restricted to the requesting user's own record (by email)?
    is_self_query = bool(email) and normalize_text(email) in query_text

    # Rule 2: personal-sensitive columns are self-only.
    requested_sensitive = [
        col for col in SELF_ONLY_COLUMNS if re.search(rf"\b{col}\b", lower_query)
    ]
    if requested_sensitive and not is_self_query:
        logger.warning(f"RBAC: blocked sensitive columns for non-self query | cols={requested_sensitive}")
        return False, (
            "I can't share colleagues' personal details such as salary, performance rating, "
            "or leave balances. I can only provide those for your own record."
        )

    # Rule 3: department scoping. Reject the leaky LIKE-on-dept_id pattern.
    if re.search(r"dept_id\s+like", lower_query):
        logger.warning("RBAC: rejected LIKE on dept_id")
        return False, (
            "This request could expose data outside your department, so it was blocked. "
            "Please ask about employees within your own department."
        )

    if is_self_query:
        # A query scoped to the user's own email is inherently in-scope.
        return True, ""

    allowed_ids = _allowed_dept_id_set(dept_ids)
    scope_ids = _extract_dept_scope_ids(lower_query)

    logger.info(
        f"RBAC check | tables={referenced_tables} | allowed_dept_ids={allowed_ids} "
        f"| scope_ids={scope_ids} | self={is_self_query}"
    )

    if not scope_ids:
        return False, (
            "I can only provide employee information for your own department. "
            "Please scope your question to your department."
        )

    if not scope_ids.issubset(allowed_ids):
        return False, (
            "This request appears to target a department other than your own. "
            "I can only provide information about employees in your department."
        )

    return True, ""


# Phrases that signal a company-wide / cross-department employee request.
COMPANY_WIDE_TERMS = [
    "company", "organization", "organisation", "entire", "whole",
    "all employees", "all the employees", "all department", "all departments",
    "every department", "across department", "across departments",
    "across the company", "other department", "all staff", "everyone in",
    "organization wide", "company wide",
]


def _scope_label(departments: list[str]) -> str:
    names = [d for d in (departments or []) if d]
    return ", ".join(sorted(names)) if names else "your department"


def _detect_cross_scope_request(
    query: str,
    departments: list[str],
    job_title: str,
) -> str | None:
    """
    Deterministic guard on the natural-language question.

    Returns a clear, user-facing refusal string when a non-executive user is
    explicitly asking about the whole company or a department other than their
    own; returns None when the request is within the user's own scope.

    This runs BEFORE SQL generation so such requests are answered with an honest
    "out of scope" message instead of being silently narrowed to the user's
    department (which previously mislabelled a department count as a company
    total, or returned 0 for another department).
    """
    if has_elevated_access(job_title):
        return None

    q = normalize_text(query)
    own_names = {normalize_text(d) for d in (departments or []) if d}
    scope_label = _scope_label(departments)

    # Questions explicitly limited to the user's own team are always in scope.
    asks_own = bool(re.search(r"\bmy (department|dept|team|colleagues|coworkers|peers)\b", q))
    if asks_own:
        return None

    # Company-wide / all-departments intent.
    if any(term in q for term in COMPANY_WIDE_TERMS):
        return (
            f"I can only share employee information for your own department ({scope_label}). "
            f"I can't provide company-wide or cross-department employee data."
        )

    # A specific department named in the question that is not the user's own.
    foreign = []
    for name in DEPARTMENT_NAME_TO_ID:
        if name == "general":  # shared/general scope, not department-private
            continue
        if name in own_names:
            continue
        if re.search(rf"\b{re.escape(name)}\b", q):
            foreign.append(name)

    if foreign:
        nice = ", ".join(n.title() for n in sorted(foreign))
        return (
            f"I can only share employee information for your own department ({scope_label}), "
            f"not the {nice} department."
        )

    return None




# SQL PROMPT
strict_sql_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        (
            "You are a SQLite expert.\n"
            "Generate a single, syntactically correct SQLite SELECT query.\n\n"

            "CRITICAL RULES:\n"

            "1. ONLY generate SELECT queries.\n"
            "2. NEVER generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or TRUNCATE statements.\n"
            "3. Use case-insensitive matching with LOWER(column) = LOWER('value') for text filters.\n"
            "4. Limit results to top {top_k} rows unless the user explicitly asks for a count or 'all'.\n"
            "5. ONLY output raw executable SQL. No markdown, no code fences, no explanation.\n"
            "6. ONLY use table and column names that appear in the Database Schema below. "
               "Never invent tables (e.g. 'leave_policies', 'payroll') or columns.\n"
            "7. NEVER write 'SELECT *'. Always list the explicit columns the question needs.\n"
            "8. NEVER select the 'hashed_password' column.\n"
            "9. Resolve 'my', 'me', or 'I' to the current user using the literal Email value from "
               "the User Profile Context: filter with LOWER(employees.email) = LOWER('<that email>'). "
               "NEVER use placeholders like 'current_user' or 'session_user'.\n\n"

            "MANDATORY DEPARTMENT SCOPING (employees table):\n"
            "0. SCOPING APPLIES ONLY WHEN 'Access Level: STANDARD'. If the User Profile Context "
               "says 'Access Level: EXECUTIVE', the user may query across ALL departments and the "
               "whole company: do NOT add any department-scope clause, and ignore rules 11-14.\n"
            "10. 'employees.dept_id' is a JSON ARRAY of department ids (e.g. [1,3]).\n"
            "11. For EVERY query on the employees table you MUST restrict rows to the current "
                "user's department(s) using EXACTLY this membership clause, substituting the "
                "Department IDs from the User Profile Context:\n"
                "    EXISTS (SELECT 1 FROM json_each(employees.dept_id) WHERE value IN (<Department IDs>))\n"
                "12. The ONLY exception to rule 11 is a question about the current user themselves "
                "(e.g. 'my salary', 'my leave balance'): in that case filter by the user's own email "
                "instead.\n"
            "13. NEVER use LIKE on dept_id (e.g. dept_id LIKE '%N%'); it matches ids that merely "
                "share digits (1 matches 10, 11, 21...) and leaks data across departments.\n"
            "14. Use ONLY the Department IDs given in the User Profile Context. Never guess or widen "
                "the department scope, and never scope to a different department even if the question "
                "names one.\n\n"

            "EXAMPLES (reproduce this exact scoping style, substituting the real "
            "Department IDs / Email from the User Profile Context):\n"
            "- Q: How many employees are in my department?  [Department IDs: 3]\n"
            "  SQL: SELECT COUNT(*) FROM employees WHERE EXISTS "
            "(SELECT 1 FROM json_each(employees.dept_id) WHERE value IN (3));\n"
            "- Q: List the employees in my department  [Department IDs: 3]\n"
            "  SQL: SELECT emp_name, job_title FROM employees WHERE EXISTS "
            "(SELECT 1 FROM json_each(employees.dept_id) WHERE value IN (3)) LIMIT 5;\n"
            "- Q: What is the email of <colleague>?  [Department IDs: 3]\n"
            "  SQL: SELECT emp_name, email FROM employees WHERE LOWER(emp_name) = LOWER('<colleague>') "
            "AND EXISTS (SELECT 1 FROM json_each(employees.dept_id) WHERE value IN (3));\n"
            "- Q: What is my leave balance?  [Email: jane.doe@example.com]\n"
            "  SQL: SELECT leaves_balance FROM employees WHERE "
            "LOWER(employees.email) = LOWER('jane.doe@example.com');\n\n"

            "Database Schema:\n"
            "{table_info}"
        )
    ),
    ("human", "{input}")
])


# SQL QUERY CHAIN
# A direct prompt -> model -> text chain gives us full control over the schema
# context and security rules (instead of create_sql_query_chain, which would
# inject its own, broader, table metadata).
sql_chain = strict_sql_prompt | model | StrOutputParser()


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
        dept_id_raw = configurable.get("dept_id")
        if isinstance(dept_id_raw, (list, tuple)):
            dept_ids = [str(d) for d in dept_id_raw if d is not None and str(d).strip()]
        elif dept_id_raw is None or str(dept_id_raw).strip() == "":
            dept_ids = []
        else:
            dept_ids = [str(dept_id_raw)]

        # Honest out-of-scope guard: refuse company-wide / other-department
        # employee requests up front instead of silently narrowing them to the
        # user's own department (which produced misleading answers).
        scope_refusal = _detect_cross_scope_request(query, departments, job_title)
        if scope_refusal:
            logger.info(f"Cross-scope request refused by NL guard | query={query!r}")
            return scope_refusal

        access_level = "EXECUTIVE" if has_elevated_access(job_title) else "STANDARD"

        enriched_query = (
            "User Profile Context (use these literal values to resolve 'my', 'me', "
            "or the current user - e.g. filter by the user's email or department):\n"
            f"- Name: {emp_name}\n"
            f"- Email: {email}\n"
            f"- Departments: {', '.join(departments) if departments else 'N/A'}\n"
            f"- Department IDs (employees.dept_id is a JSON array of these ids): "
            f"{', '.join(dept_ids) if dept_ids else 'N/A'}\n"
            f"- Access Level: {access_level}\n\n"
            f"User Question: {query}"
        )


        # STEP 1: Generate SQL from LLM
        sql_query = sql_chain.invoke({
            "input": enriched_query,
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

        rbac_ok, rbac_message = enforce_rbac(clean_query, departments, job_title, email, dept_ids)
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
