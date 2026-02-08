# FastAPI Entry point
from fastapi import FastAPI
from pydantic import BaseModel
from .core.config import settings # We'll assume this loads your .env
import asyncio
import csv
import io
from uuid import uuid4
from typing import List, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.agent import agent_app, AgentState
from app.storage import save_job, get_job

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
    # Placeholder: We will connect LangGraph here in the next step
    return {
        "response": f"Received query: {request.user_query}",
        "thought_process": ["Supervisor received request", "Routing to Finance Agent..."],
        "action": "Analyzing Mock Data"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)