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