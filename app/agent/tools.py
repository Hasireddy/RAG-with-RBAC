from langchain.tools import tool
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig

from rag.get_api_response import get_response

# Define Tools/Abilities
# Define state
# Define nodes
# Define Graph/connections


db = SQLDatabase.from_uri("sqlite:///Chinook.db")

#llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

model = init_chat_model(
    "gpt-4o-mini",
    temperature=0
)


sql_agent = create_sql_agent(
    model=model,
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



