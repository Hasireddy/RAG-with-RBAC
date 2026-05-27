# Step 3: Define model node
from langchain.chat_models import init_chat_model
from langgraph.graph import MessagesState
from langchain_core.messages import (
    SystemMessage,
    ToolMessage,
    HumanMessage
)
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from IPython.display import Image, display
from langgraph.checkpoint.memory import InMemorySaver
from .tools import rag_tool, sql_tool




model = init_chat_model(
    "gpt-4o-mini",
    temperature=0
)


# Augment the LLM with agent
tools = [rag_tool, sql_tool]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)


# Define model node
# Each node takes a state and returns state object

def brain(state: dict):
    """LLM decides whether to call a tool or not"""

    return {
        "messages": [
            model_with_tools.invoke(
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
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }


# Define tool node - Tool executor
# Tool executor after executing a tool returns state message with updated state
#tool node performs state call. takes the existing state, performs tool calls and appends the updated state
#and returns the state object

tool_node = ToolNode(tools)


checkpointer = InMemorySaver()

# Build Graph
agent_builder = StateGraph(MessagesState)

# add nodes
agent_builder.add_node("brain")
agent_builder.add_node("tools", tool_node)

# add edges
agent_builder.add_edge(START, "brain")
agent_builder.add_edge("tools", "brain")
agent_builder.add_conditional_edges("brain",tools_condition)

graph = agent_builder.compile(checkpointer=checkpointer)


# Show the agent
display(Image(graph.get_graph(xray=True).draw_mermaid_png()))


#invoke graph
def run_agent(query: str, thread_id: str):
    response = graph.invoke(
        {
            "messages": [
                HumanMessage(content=query)
            ]
        },
        {
            "configurable": {
                "thread_id": thread_id
            }
        }
    )

    return response["messages"][-1].content


