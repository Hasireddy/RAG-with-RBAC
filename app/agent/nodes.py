# Step 3: Define model node
from langchain.messages import SystemMessage
from langchain.chat_models import init_chat_model
from .tools import rag_tool, sql_tool




model = init_chat_model(
    "gpt-4o-mini",
    temperature=0
)


# Augment the LLM with agent
tools = [rag_tool, sql_tool]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)



def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""

    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant tasked with performing arithmetic on a set of inputs."
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }