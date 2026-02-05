# The Main Orchestrator
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings

# 1. Define the Options
# We are telling the LLM: "You can ONLY choose one of these two workers."
# It's like a dropdown menu for the AI.
options = ["Finance_Agent", "Operations_Agent"]

# 2. Define the Output Format
# We force the LLM to return a structured JSON, not just random text.
# This makes it reliable. If it just chats, the code breaks.
class RouteQuery(BaseModel):
    """Route the user's query to the most relevant worker."""
    destination: Literal["Finance_Agent", "Operations_Agent"] = Field(
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