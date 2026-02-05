# The Main Orchestrator
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
import operator
from typing import Annotated, List, TypedDict, Union

# Define the shared state of the agent workflow
class AgentState(TypedDict):
    # The full conversation history (allows the agent to remember context)
    messages: Annotated[List[str], operator.add]
    
    # The "Next Step" logic - who acts next?
    next_step: str
    
    # Context data pulled from GraphRAG or ERP
    current_context: dict
    
    # The final structured report for the frontend
    final_report: dict

# 1. Define the Options
# We are telling the LLM: "You can ONLY choose one of these two workers."
# It's like a dropdown menu for the AI.
options = ["Finance_Agent", "Operations_Agent", "Risk_Agent"]

# 2. Define the Output Format
# We force the LLM to return a structured JSON, not just random text.
# This makes it reliable. If it just chats, the code breaks.
class RouteQuery(BaseModel):
    """Route the user's query to the most relevant worker."""
    destination: Literal["Finance_Agent", "Operations_Agent", "Risk_Agent"] = Field(
        ..., 
        description="Choose Finance for money/tax/invoices. Choose Operations for stock/shipping/vendors."
    )

# 3. The Supervisor Function
def supervisor_node(state):
    # Get the latest message from the user
    messages = state["messages"]
    
    # Initialize the LLM (The Brain)
    llm = ChatOpenAI(model=settings.MODEL_NAME, temperature=0)
    
    # Bind the "RouteQuery" structure so the LLM knows it MUST fill this form
    structured_llm = llm.with_structured_output(RouteQuery)
    
    # The System Prompt (The Instructions)
    system_prompt = SystemMessage(content="""
        You are the Main Orchestrator for the ERP Intelligence Layer.
        Your job is to route the user's request to the correct specialist.
        
        - If the user asks about money, invoices, or budget -> Finance_Agent
        - If the user asks about stock, items, or shipping -> Operations_Agent
        - If the user asks about risk, anomalies, or alerts -> Risk_Agent
        
        Do not try to answer the question yourself. Just route it.
    """)
    
    # Run the AI
    decision = structured_llm.invoke([system_prompt] + messages)
    
    # Return the decision to the shared state
    # We update the 'next_step' variable so the graph knows where to go
    return {"next_step": decision.destination}

def finance_agent(state):

    message: state["messages"]

    finance_prompt = SystemMessage(content="""
        You are the Finance Agent for the ERP Intelligence Layer.
        Your job is to answer the user's request about money, invoices, or budget.
    """)

    response = llm.invoke([finance_prompt] + messages)
    return {"messages": [response]}

def operations_agent(state: AgentState):
    messages = state["messages"]
    llm = ChatOpenAI(model=settings.MODEL_NAME, temperature=0)
    ops_llm = llm.bind_tools(operations_tools)
    
    operations_prompt = SystemMessage(content="""
    You are the Operations Agent. Manage stock and vendors.""")

    response = ops_llm.invoke([operations_prompt] + messages)
    return {"messages": [response]}

def risk_agent(state: AgentState):
    messages = state["messages"]
    llm = ChatOpenAI(model=settings.MODEL_NAME, temperature=0)
    risk_llm = llm.bind_tools(risk_tools)
    
    risk_prompt = SystemMessage(content="""
    You are the Risk Agent. Manage stock and vendors.""")
    
    response = risk_llm.invoke([risk_prompt] + messages)
    return {"messages": [response]}

workflow = StateGraph(AgentState)

workflow.add_node("supervisor", supervisor_node)
workflow.add_node("finance_agent", finance_agent)
workflow.add_node("operations_agent", operations_agent)
workflow.add_node("risk_agent", risk_agent)

workflow.set_entry_point("supervisor")

workflow.add_conditional_edges(
    "supervisor",
    lambda state: state["next_step"],
    {
        "Finance_Agent": "finance_agent",
        "Operations_Agent": "operations_agent",
        "Risk_Agent": "risk_agent"
    }
)

workflow.add_edge("finance_agent", END)
workflow.add_edge("operations_agent", END)
workflow.add_edge("risk_agent", END)

app = workflow.compile()