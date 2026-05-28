from dotenv import load_dotenv
from langchain.tools import tool
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_sql_query_chain
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
import os
import re
import traceback
from langchain_core.tools import tool
from app.rag.get_api_response import get_response

# Define Tools/Abilities
# Define state
# Define nodes
# Define Graph/connections


# Load environment variables
load_dotenv()  # reads variables from a .env file and sets them in os.environ
api_key = os.getenv("API_KEY")



model = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
    api_key=api_key
)




@tool
def rag_tool(query: str) -> str:
    """
       Search enterprise company documents and answer questions.
       Use for policies, documentation, employee knowledge,
       and unstructured text information.
       """

    #state = config["configurable"]

    result = get_response(
        query=query,
        session_id="TEMP",  # replaced by graph/state layer if needed
        emp_name="TEMP",
        email="TEMP",
        departments=[]
    )

    return str(result)


# 1. DEFENSIVE PATHING: Look for the file in the exact current working directory
current_dir = os.getcwd()
db_file_path = os.path.join(current_dir, "company_database.db")

print(f"👉 CHATBOT IS TRYING TO READ DATABASE AT: {db_file_path}")
print(f"👉 DOES FILE EXIST? {os.path.exists(db_file_path)}")


try:
    db = SQLDatabase.from_uri(f"sqlite:///{db_file_path}")
    # Inspect table structures
    print(f"👉 FOUND TABLES IN DATABASE: {db.get_usable_table_names()}")
except Exception as init_err:
    print(f"❌ DATABASE INITIALIZATION CRASHED: {str(init_err)}")
    db = None


# Force the LLM to use case-insensitive matching because names vary
#Fix variable names to match LangChain requirements: 'input', 'table_info', 'top_k'

strict_sql_prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a SQLite expert. Given an input question, create a syntactically correct SQLite query.\n"
        "CRITICAL RULES:\n"
        "1. Always use case-insensitive matching (e.g., LOWER(department) = 'sales' or department LIKE '%sales%') "
        "to ensure spelling and capitalization mismatches do not cause empty returns.\n"
        "2. Limit your query to the top {top_k} results unless specified otherwise.\n"
        "3. ONLY output the executable SQL query string. Do not include markdown wraps or explanations.\n\n"
        "Database Schema:\n{table_info}"
    )),
    ("human", "{input}")  # Changed from {question} to {input}
])

# ADD THESE 4 LINES HERE: Instantiate the query chain so it can be invoked inside the tool
sql_chain = create_sql_query_chain(
    llm=model,
    db=db,
    prompt=strict_sql_prompt
)


@tool
def sql_tool(query: str) -> str:
    """
    Query structured SQLite database.
    Use for counts, aggregations, analytics,
    filtering, and tabular data.
    """
    if db is None:
        return "System Error: SQL Database initialization failed. Check server logs."

    try:
        # 1. Generate the SQL query string using the chain
        sql_query = sql_chain.invoke({"question": query})
        print(f"👉 GENERATED SQL QUERY RAW: {sql_query}")

        # ROBUST FIX: Extract everything starting from the first SQL keyword (SELECT/with/etc)
        clean_query = sql_query

        # Strip out markdown formatting ```sql ... ```
        clean_query = clean_query.replace("```sql", "").replace("```", "").strip()

        # Use regex to find the true beginning of the SQL command (ignoring conversational headers)
        match = re.search(r'\b(SELECT|WITH|INSERT|UPDATE|DELETE)\b', clean_query, re.IGNORECASE)
        if match:
            clean_query = clean_query[match.start():]

        print(f"👉 EXECUTING CLEAN SQL QUERY: {clean_query}")

        # 2. Run the cleaned SQL query text against the database
        execution_result = db.run(clean_query)
        print(f"👉 DATABASE ROW OUTPUT: {execution_result}")

        if execution_result is None or str(execution_result).strip() in ["", "[]", "()"]:
            return "Database verification: 0 records match this criteria. The department or list is empty."

        return str(execution_result)

    except Exception as e:
        print("❌ SQL TOOL ROW EXECUTION ERROR:")
        traceback.print_exc()
        return f"Database query failed. Technical details: {str(e)}"
