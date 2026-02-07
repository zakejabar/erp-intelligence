# FastAPI Entry point
from fastapi import FastAPI
from pydantic import BaseModel
from app.core.config import settings # We'll assume this loads your .env

app = FastAPI(title="ERP Intelligence Layer", version="1.0.0")

# Input Schema for the Frontend
class QueryRequest(BaseModel):
    user_query: str
    user_id: str

@app.get("/")
async def root():
    return {"status": "System Online", "mode": "Mock Data Enabled"}

@app.post("/v1/agent/run")
async def run_agent(request: QueryRequest):
    from app.agents.agent import app as agent_app
    
    # 1. Prepare the input for the agent
    initial_state = {
        "messages": [HumanMessage(content=request.user_query)]
    }
    
    # 2. Run the graph
    result = agent_app.invoke(initial_state)
    
    # 3. Extract the final response
    # The last message in the 'messages' list is the AI's answer
    final_message = result["messages"][-1].content
    
    return {
        "response": final_message,
        "thought_process": [str(m) for m in result["messages"]], # metrics/debug
        "action": "Agent Execution Complete"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)