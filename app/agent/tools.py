from langchain.tools import tool
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain.chat_models import init_chat_model
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
def rag_tool(input: dict) -> str:
    return get_response(
        query=input["query"],
        session_id=input["session_id"],
        emp_name=input["emp_name"],
        email=input["email"],
        departments=input["departments"],
    )["answer"]


@tool
def sql_tool(query: str) -> str:
    return sql_agent.invoke({"input": query})["output"]



