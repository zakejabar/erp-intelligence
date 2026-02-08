# backend/app/agents/agent.py

import operator
from typing import Annotated, List, Literal, TypedDict, Union

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langgraph.graph import StateGraph, END

# Import your settings
from app.core.config import settings

# --- CRITICAL: Import Tools or Comment them out if tools.py isn't ready yet ---
# from app.agents.tools import operations_tools, risk_tools, finance_tools 
# FOR NOW: I will define empty lists so the code doesn't crash while you build tools.py
# operations_tools = [] 
# risk_tools = []

# State definition
class AgentState(TypedDict):
    # The full conversation history
    messages: Annotated[List[BaseMessage], operator.add]
    # The "Next Step" logic - who acts next?
    next_step: str
    # Context data pulled from GraphRAG or ERP (Optional for now)
    current_context: dict
    # The final structured report for the frontend (Optional for now)
    final_report: dict

    file_input: str

# Supervisor (Router)
class RouteQuery(BaseModel):
    """Route the user's query to the most relevant worker."""
    destination: Literal["Finance_Agent", "Operations_Agent", "Risk_Agent"] = Field(
        ..., 
        description="Choose Finance for money/tax/invoices. Operations for stock/shipping. Risk for fraud/alerts."
    )

def supervisor_node(state):
    messages = state["messages"]
    llm = ChatGoogleGenerativeAI(model=settings.MODEL_NAME, temperature=0)
    
    # BIND OUTPUT: Force the LLM to choose one of our 3 agents
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
    llm = ChatGoogleGenerativeAI(model=settings.MODEL_NAME, temperature=0)

    if finance_tools:
        llm = llm.bind_tools(finance_tools)
    
    finance_prompt = SystemMessage(content="""
        You are the Finance Agent for the ERP Intelligence Layer.
        Your job is to answer the user's request about money, invoices, or budget.
    """)
    
    response = llm.invoke([finance_prompt] + messages)
    return {"messages": [response]}

def operations_agent(state: AgentState):
    messages = state["messages"]
    llm = ChatGoogleGenerativeAI(model=settings.MODEL_NAME, temperature=0)
    
    # FIX 2: Check if tools exist to avoid crash
    if operations_tools:
        llm = llm.bind_tools(operations_tools)
    
    operations_prompt = SystemMessage(content="""
    You are the Operations Agent. Manage stock and vendors.""")

    # FIX 3: Invoke the LLM that has tools bound (reassigned above)
    response = llm.invoke([operations_prompt] + messages)
    return {"messages": [response]}

def risk_agent(state: AgentState):
    messages = state["messages"]
    llm = ChatGoogleGenerativeAI(model=settings.MODEL_NAME, temperature=0)
    
    if risk_tools:
        llm = llm.bind_tools(risk_tools)
    
    risk_prompt = SystemMessage(content="""
    You are the Risk Agent. Analyze transaction anomalies and flag fraud risks.""")
    
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