# Step 3: Define model node
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    SystemMessage,
    ToolMessage,
    HumanMessage
)
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from .tools import rag_tool, sql_tool
from .state import MessagesState
import os


# Load environment variables
load_dotenv()  # reads variables from a .env file and sets them in os.environ
api_key = os.getenv("API_KEY")


model = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
    api_key=api_key
)


# Augment the LLM with agent
tools = [rag_tool, sql_tool]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)

# Define tool node - Tool executor
# Tool executor after executing a tool returns state message with updated state
#tool node performs state call. takes the existing state, performs tool calls and appends the updated state
#and returns the state object

tool_node = ToolNode(tools)


# Define model node
# Each node takes a state and returns state object

def brain(state: MessagesState):
    """LLM decides whether to call a tool or not"""

    messages = state.get("messages", [])

    response = model_with_tools.invoke(
                [
                    SystemMessage(
                        content="""
                                    You are an intelligent enterprise AI assistant.
                                
                                    You have access to:
                                
                                    1. rag_tool
                                    - Use for company policies
                                    - documentation
                                    - employee information
                                    - unstructured knowledge
                                
                                    2. sql_tool
                                    - Use for structured database queries
                                    - analytics
                                    - counts
                                    - aggregations
                                    - filtering
                                    - tabular data
                                
                                    Choose the correct tool when needed.
                                    Use tools before answering if information is required.
                                """
                    )
                ]
                + state["messages"]
            )

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }



checkpointer = InMemorySaver()

# Build Graph workflow
agent_builder = StateGraph(MessagesState)

# add nodes
agent_builder.add_node("brain", brain)
agent_builder.add_node("tools", tool_node)

# add edges to connect nodes
agent_builder.add_edge(START, "brain")

agent_builder.add_conditional_edges("brain",tools_condition, {
        "tools": "tools",
        "__end__": END
    })

agent_builder.add_edge("tools", "brain")

graph = agent_builder.compile(checkpointer=checkpointer)


#invoke graph
def run_agent(query: str, session_id: str, emp_name: str, email: str, departments: list[str]):
    response = graph.invoke(
        {
            "messages": [
                HumanMessage(content=query)
            ],
            "session_id": session_id,
            "emp_name": emp_name,
            "email": email,
            "departments": departments,
            "llm_calls": 0

            },
        {
                "configurable":
                    {
                        "thread_id": session_id,
                        "session_id": session_id,
                        "emp_name": emp_name,
                        "email": email,
                        "departments": departments,
                    }
                }
        )

    last_msg = response["messages"][-1]

    return {
        "message": {
            "content": last_msg.content,
            "type": getattr(last_msg, "type", "ai")
        },
        "session_id": session_id,
        "llm_calls": response.get("llm_calls", 0)
    }


