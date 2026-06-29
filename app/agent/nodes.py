# Step 3: Define model node
import os
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

from .query_classifier import detect_query_type_llm



# Load environment variables
load_dotenv()  # reads variables from a .env file and sets them in os.environ
api_key = os.getenv("API_KEY")


model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3,
    api_key=api_key,
    streaming=True
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
    job_title = state.get("job_title", "Unknown")
    departments = state.get("departments", [])
    query_type = state.get("query_type", "UNSPECIFIED")


    system_prompt = f"""
         You are a role-aware AI assistant for a company.
         This query has been classified as : {query_type}.
         Active user job title: {job_title}
         
         Your task :
         - Answer a user's question using the provided USERINFO, DOCUMENT CONTEXT and tools.
         - Follow the TOOL SELECTION RULES and IDENTITY RULES strictly.
         - Be concise, clear and professional.
        
         ACTIVE USER INFO:
         - Name: {emp_name}
         - Email: {email}
         - Departments: {departments}
                                
         TOOL SELECTION RULES (follow strictly):
         
        - If the query is about specific records, metrics, counts, trends, KPIs, employee data, department data,
          or financial figures, you MUST prefer sql_tool.
        - If the query is conceptual, explanatory, policy, procedural, documentation, FAQ, or knowledge-base related,
          you MUST prefer rag_tool.
        - If query_type is "SQL", choose sql_tool unless the requested data is unavailable or unauthorized.
        - If query_type is "RAG", choose rag_tool and DO NOT use sql_tool.
        
        1. Use sql_tool for ANY question involving:
           - Employee details (name, email, phone, department, role, salary)
           - Leave balances, attendance, performance ratings
           - Company financials, headcount, analytics
           - Anything that sounds like a database lookup
           
           Examples:
           - "What is the email of <person>?" → sql_tool
           - "How many employees are in the company / my department / finance?" → sql_tool
           - "What is my (or someone's) salary / leave balance?" → sql_tool
           
           Do NOt decide access yourself. NEVER refuse,narrow, or pre-judge a data question
           based on who the user is, what department it concerns, or whether a field looks sensitive. 
           ALWAYS call sql_tool and let it decide. sql_tool enforces all access rules deterministically
           (including full access for executives) and returns EITHER the requested data OR a ready-to-show message.
           Your job is only to call it and relay its result.
        
        2. Use rag_tool for ANY question involving:
           - Company policies, HR guidelines
           - Architecture and technical documentation
           - Onboarding, processes, internal manuals
           Examples:
           - "What is the PTO policy?" → rag_tool
           - "Why did FinSolve choose microservices?" → rag_tool
        
        3. TOOL usage requirement:
           - ALWAYS call a tool before answering if the question requires
           looking up data. Never answer employee or database questions
           from memory, and never refuse such a question on your own- the
           tool is the sole authority on what may be returned.
        
        4. Authorization, access and availability messages:
           - The tools (sql_tool / rag_tool) return ready-to-show messages. If a
           tool result is an access, permission, or availability message - for
           example it mentions "department", "access", "permission", "can only",
           "cannot", "isn't available", "for security reasons", or "not have
           access" - return that message to the user VERBATIM.
           
           - Do NOT replace it with the generic not-found message below, and do NOT
           try to work around it or fabricate data.

        - If a tool returns actual data (e.g. a count, a row, a value), answer the
           user's question directly using that data. A returned count of 0 means
           "none found", not an error.  
           
        - If the answer is genuinely not found by any tool ( and it is not
           an authorization failure) respond explicitly:
           "I'm sorry, I can only answer questions related to company documents and tools."
        
        - If a SQL query would require unauthorized or missing schema data, do not expose raw SQL or raw errors.
           Return a safe explanation or fallback to a RAG-style answer.
           
        CRITICAL IDENTITY RULE:
        For questions about the current user (e.g., leave balance, rating),
        use the ACTIVE USER INFO above and pass it to sql_tool.
        
        CRITICAL TEXT GENERATION RULES:
        1. Never confuse leaves_taken (already used) with leaves_balance (remaining).
        2. If leaves_balance is 0, explicitly state the user has 0 days remaining.
        3. Report numbers exactly as returned by sql_tool. Do not relabel the result's scope- if
            the tool's message describes the data as belonging to a specific department, keep the
            wording;never call a department-level figure a company-wide total or vice versa.
        
        When responding:
        - Clearly and directly answer the user's question.
        - Briefly reference the source(.g.; "Based on company records...." without exposing raw tool output.
                                              
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
def run_agent(query: str, session_id: str, emp_id: str, emp_name: str, email: str, job_title: str, departments: list[str],dept_id=None):
    query_type = detect_query_type_llm(query)

    response = graph.invoke(
        {
            "messages": [
                HumanMessage(content=query)
            ],
            "session_id": session_id,
            "emp_id": emp_id,
            "emp_name": emp_name,
            "email": email,
            "job_title": job_title  ,
            "departments": departments,
            "query_type": query_type,
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
                    "job_title": job_title,
                    "departments": departments,
                    "dept_id":dept_id
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


