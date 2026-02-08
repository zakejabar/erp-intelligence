# FastAPI Entry point
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import shutil
import os
from pydantic import BaseModel
from app.agents.config import settings # We'll assume this loads your .env
import asyncio
import csv
import io
from uuid import uuid4
from typing import List, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.agents.agent import agent_app, AgentState

app = FastAPI(title="ERP Intelligence Layer", version="1.0.0")

# # Input Schema for the Frontend
# class QueryRequest(BaseModel):
#     user_query: str
#     user_id: str
#     user_file: UploadFile = File(...)

# @app.get("/")
# async def root():
#     return {"status": "System Online", "mode": "Mock Data Enabled"}

@app.post("/v1/agent/run")
async def upload_and_run(
    user_query: str = Form(...), 
    user_id: str = Form(...), 
    user_file: UploadFile = File(...)
):
    
    os.makedirs("data_mocks", exist_ok=True)
    file_location = f"data_mocks/{user_file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(user_file.file, file_object)
    
    # Start the Graph with the file path in the state
    initial_state = {
        "messages": [HumanMessage(content=user_query)],
        "file_input": file_location # This is the 'workspace' for the agents!
    }
    
    # Run the LangGraph app
    result = agent_app.invoke(initial_state)
    
    return {
        "answer": result["messages"][-1].content,
        "agent_used": result.get("next_step", "Unknown")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)