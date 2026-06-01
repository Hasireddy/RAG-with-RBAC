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
    # Extract user metadata from the active user state

    emp_name = state.get("emp_name", "Unknown")
    email = state.get("email", "Unknown")
    departments = state.get("departments", [])

    system_prompt = f"""
         You are technical documentation expert and AI assistant for a company.
         Your task is to help answer a user's question using the provided USERINFO, DOCUMENT CONTEXT and tools.
        
     
                                ACTIVE USER INFO:
                                - Name: {emp_name}
                                - Email: {email}
                                - Departments: {departments}
                                
         TOOL SELECTION RULES (follow strictly):
        
        1. Use sql_tool for ANY question involving:
           - Employee details (name, email, phone, department, role, salary)
           - Leave balances, attendance, performance ratings
           - Company financials, headcount, analytics
           - Anything that sounds like a database lookup
           Examples:
           - "What is the email of Stephen?" → sql_tool
           - "How many employees are in engineering?" → sql_tool
           - "What is my leave balance?" → sql_tool
        
        2. Use rag_tool for ANY question involving:
           - Company policies, HR guidelines
           - Architecture and technical documentation
           - Onboarding, processes, internal manuals
           Examples:
           - "What is the PTO policy?" → rag_tool
           - "Why did FinSolve choose microservices?" → rag_tool
        
        3. ALWAYS call a tool before answering if the question requires
           looking up data. Never answer employee or database questions
           from memory.
        
        4. If the answer is not found by any tool, respond exactly:
           "I'm sorry, I can only answer questions related to company documents and tools."
        
        CRITICAL IDENTITY RULE:
        For questions about the current user (e.g., leave balance, rating),
        use the ACTIVE USER INFO above and pass it to sql_tool.
        
        CRITICAL TEXT GENERATION RULES:
        1. Never confuse leaves_taken (already used) with leaves_balance (remaining).
        2. If leaves_balance is 0, explicitly state the user has 0 days remaining.
                                            
    """


    response = model_with_tools.invoke(
                [
                    SystemMessage(
                        content=system_prompt
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
def run_agent(query: str, session_id: str, emp_id: str, emp_name: str, email: str, departments: list[str]):
    response = graph.invoke(
        {
            "messages": [
                HumanMessage(content=query)
            ],
            "session_id": session_id,
            "emp_id": emp_id,
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
                        "emp_id": emp_id,
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


