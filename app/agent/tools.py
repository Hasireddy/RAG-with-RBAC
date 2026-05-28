from dotenv import load_dotenv
from langchain.tools import tool
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
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
    model="gpt-4o-mini",
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

# ADD THESE 4 LINES HERE: Instantiate the query chain so it can be invoked inside the tool
sql_chain = create_sql_query_chain(
    llm=model,
    db=db
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

        if not execution_result:
            return "No matching records found in the database."

        return str(execution_result)

    except Exception as e:
        print("❌ SQL TOOL ROW EXECUTION ERROR:")
        traceback.print_exc()
        return f"Database query failed. Technical details: {str(e)}"
