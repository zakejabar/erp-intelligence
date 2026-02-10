# backend/app/agents/agent.py
from dotenv import load_dotenv
load_dotenv()
import operator
from typing import Annotated, List, Literal, TypedDict, Union

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langgraph.graph import StateGraph, END
import os

# Import your settings
from app.agents.config import settings
from app.agents.tools import get_open_invoices, process_file


operations_tools = [process_file] 
risk_tools = [process_file]

# State definition
class AgentState(TypedDict):
    # The full conversation history
    messages: Annotated[List[BaseMessage], operator.add]
    # The "Next Step" logic - who acts next?
    next_step: str
    # Context data pulled from GraphRAG or ERP (Optional for now)
    current_context: dict

    file_input: str
    # The final structured report for the frontend (Optional for now)
    final_report: dict

    

# Supervisor (Router)
# No change needed here if import was swapped. I will check terminal first.

class RouteQuery(BaseModel):
    """Route the user's query to the most relevant worker."""
    destination: Literal["Finance_Agent", "Operations_Agent", "Risk_Agent"] = Field(
        ..., 
        description="Choose Finance for money/tax/invoices. Operations for stock/shipping. Risk for fraud/alerts."
    )

def supervisor_node(state):
    messages = state["messages"]
    llm = ChatGoogleGenerativeAI(model=settings.MODEL_NAME, google_api_key=settings.GEMINI_API_KEY, temperature=0)
    
    # LLM choose one of our 3 agents
    structured_llm = llm.with_structured_output(RouteQuery)
    
    system_prompt = SystemMessage(content="""
        You are the Main Orchestrator for the ERP Intelligence Layer.
        Your job is to route the user's request to the correct specialist.
        
        - If the user asks about money, invoices, or budget -> Finance_Agent
        - If the user asks about stock, items, or shipping -> Operations_Agent
        - If the user asks about risk, anomalies, or alerts -> Risk_Agent
        
        Do not try to answer the question yourself. Just route it.
    """)
    
    decision = structured_llm.invoke([system_prompt] + messages)
    return {"next_step": decision.destination}

# --- 3. THE WORKER AGENTS ---

def finance_agent(state: AgentState):
    # FIX 1: Typo fixed (message -> messages)
    messages = state["messages"]
    llm = ChatGoogleGenerativeAI(model=settings.MODEL_NAME, google_api_key=settings.GEMINI_API_KEY, temperature=0)

    llm_with_tools = llm.bind_tools([get_open_invoices, process_file])

    file_path = state.get("file_input", "No file uploaded")

    file_content = ""
    if file_path and os.path.exists(file_path):
        file_content = process_file(file_path)
    
    finance_prompt = SystemMessage(content=f"""
        You are an expert Finance Analyst Agent.
        
        CONTEXT:
        The user has uploaded a file (likely an invoice, receipt, or financial report).
        The content of this file is provided below.
        
        FILE CONTENT:
        -------------------------------------------
        {file_content}
        -------------------------------------------
        
        YOUR TASK:
        Analyze the file content above in the context of the user's latest message. 
        - If the user asks for specific details (dates, amounts, vendor), extract them accurately.
        - If the file content is empty or unreadable, politely inform the user.
        - Ignore any irrelevant data in the file.
        
        Answer concisely and professionally.
    """)
    
    response = llm_with_tools.invoke([finance_prompt] + messages)
    return {"messages": [response]}

def operations_agent(state: AgentState):
    messages = state["messages"]
    llm = ChatGoogleGenerativeAI(model=settings.MODEL_NAME, google_api_key=settings.GEMINI_API_KEY, temperature=0)
    
    # FIX 2: Check if tools exist to avoid crash
    if operations_tools:
        llm = llm.bind_tools(operations_tools)
    
    file_path = state.get("file_input", "No file uploaded")
    
    operations_prompt = SystemMessage(content=f"""
    You are the Operations Agent. Manage stock and vendors.
    You have access to a file at this path: {file_path}.
    ALWAYS check the file content first if the user asks about a file.
    """)

    # FIX 3: Invoke the LLM that has tools bound (reassigned above)
    response = llm.invoke([operations_prompt] + messages)
    return {"messages": [response]}


def risk_agent(state: AgentState):
    messages = state["messages"]
    llm = ChatGoogleGenerativeAI(model=settings.MODEL_NAME, google_api_key=settings.GEMINI_API_KEY, temperature=0)
    
    if risk_tools:
        llm = llm.bind_tools(risk_tools)
    
    file_path = state.get("file_input", "No file uploaded")
    
    risk_prompt = SystemMessage(content=f"""
    You are the Risk Agent. Analyze transaction anomalies and flag fraud risks.
    You have access to a file at this path: {file_path}.
    ALWAYS check the file content first if the user asks about a file.
    """)
    
    response = llm.invoke([risk_prompt] + messages)
    return {"messages": [response]}

# --- 4. THE GRAPH DEFINITION ---

workflow = StateGraph(AgentState)

# Nodes (Title Case to match Router output)
workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("Finance_Agent", finance_agent)
workflow.add_node("Operations_Agent", operations_agent)
workflow.add_node("Risk_Agent", risk_agent)

# Entry Point
workflow.set_entry_point("Supervisor")

# Conditional Edges
workflow.add_conditional_edges(
    "Supervisor",
    lambda state: state["next_step"],
    {
        "Finance_Agent": "Finance_Agent",
        "Operations_Agent": "Operations_Agent",
        "Risk_Agent": "Risk_Agent"
    }
)

# Edges to END
workflow.add_edge("Finance_Agent", END)
workflow.add_edge("Operations_Agent", END)
workflow.add_edge("Risk_Agent", END)

# Compile
agent_app = workflow.compile()