from dotenv import load_dotenv
from langchain.tools import tool
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
import os

from app.rag.get_api_response import get_response

# Define Tools/Abilities
# Define state
# Define nodes
# Define Graph/connections


db = SQLDatabase.from_uri("sqlite:///Chinook.db")

# Load environment variables
load_dotenv()  # reads variables from a .env file and sets them in os.environ
api_key = os.getenv("API_KEY")

model = init_chat_model(
    "gpt-4o-mini",
    temperature=0,
    api_key=api_key
)


sql_agent = create_sql_agent(
    llm=model,
    db=db,
    verbose=True
)


@tool
def rag_tool(query: str, config: RunnableConfig) -> str:
    """
       Search enterprise company documents and answer questions.
       Use for policies, documentation, employee knowledge,
       and unstructured text information.
       """

    state = config["configurable"]

    return get_response(
        query=query,
        session_id=state["session_id"],
        emp_name=state["emp_name"],
        email=state["email"],
        departments=state["departments"],
    )["answer"]


@tool
def sql_tool(query: str) -> str:
    """
        Query structured SQLite database.
        Use for counts, aggregations, analytics,
        filtering, and tabular data.
        """

    return sql_agent.invoke({"input": query})["output"]



