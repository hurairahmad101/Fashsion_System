"""
FastAPI Backend for Pakistan Fashion Chatbot
Run with: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import json

from agent import run_agent

app = FastAPI(
    title="ZaibunBot - Pakistan Fashion Chatbot API",
    description="AI-powered chatbot for Pakistani fashion and festivals",
    version="1.0.0"
)

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store conversation history (in-memory, simple)
conversation_store = {}


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    input_type: str = "text"  # "text" or "voice"


class ChatResponse(BaseModel):
    response: str
    session_id: str
    input_type: str


@app.get("/")
async def root():
    return {"message": "ZaibunBot API is running! 🇵🇰👗", "status": "ok"}


@app.get("/health")
async def health_check():
    """Check if Ollama is running"""
    import requests
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = r.json().get("models", [])
        model_names = [m["name"] for m in models]
        qwen_available = any("qwen2.5" in m for m in model_names)
        return {
            "status": "healthy",
            "ollama": "connected",
            "qwen_model": "available" if qwen_available else "not found",
            "available_models": model_names
        }
    except:
        return {
            "status": "warning",
            "ollama": "not connected",
            "message": "Please run: ollama serve"
        }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint"""
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Get or create conversation history
    session_id = request.session_id
    if session_id not in conversation_store:
        conversation_store[session_id] = []
    
    history = conversation_store[session_id]
    
    # Run the agent
    response_text = run_agent(request.message, history)
    
    # Update history
    history.append({"role": "user", "content": request.message})
    history.append({"role": "assistant", "content": response_text})
    
    # Keep only last 10 exchanges
    if len(history) > 20:
        history = history[-20:]
    conversation_store[session_id] = history
    
    return ChatResponse(
        response=response_text,
        session_id=session_id,
        input_type=request.input_type
    )


@app.delete("/chat/{session_id}")
async def clear_history(session_id: str):
    """Clear conversation history for a session"""
    if session_id in conversation_store:
        del conversation_store[session_id]
    return {"message": f"History cleared for session {session_id}"}


@app.get("/festivals")
async def list_festivals():
    """Get list of all Pakistani festivals"""
    from tools import PAKISTAN_FESTIVALS
    return {
        "festivals": [
            {"key": key, "name": data["name"], "season": data["season"]}
            for key, data in PAKISTAN_FESTIVALS.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
