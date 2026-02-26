"""
FastAPI Backend for Pakistan Fashion Chatbot & GlamourGPT
Run with: uvicorn main1:app --reload --port 8000
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import json
import requests
import time

from backend.Fashoin_chatbot.backend.agent import run_agent

# ===== Local Imports =====
from backend.recommendation.outfit_recommender import recommend_outfit
from backend.vision.fabric_color import analyze_fabric
from backend.vision.virtual_tryon import virtual_tryon
from backend.recommendation.accessories import suggest_accessories
from backend.recommendation.event_planner import event_planner
from backend.services.weather import get_weather
from backend.database import engine, get_db

# ===== Add parent directory to path =====
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import Base

# ===== Create Database Tables =====
# Reset all tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# ===== FastAPI App =====
app = FastAPI(
    title="GlamourGPT - Pakistan Fashion Chatbot & Recommendation API",
    description="AI-powered chatbot for Pakistani fashion, festivals, and outfit recommendations",
    version="1.0.0"
)

# ===== CORS Middleware =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Conversation Store (In-Memory) =====
conversation_store = {}


# ===== Pydantic Models - Chatbot =====
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


# ===== Pydantic Models - Recommendation =====
class ChatRequestOld(BaseModel):
    query: str

@app.get("/")
async def root():
    return {
        "message": "GlamourGPT API is running! ",
        "status": "ok",
        "services": {
            "chatbot": "Pakistan Fashion Chatbot"
        }
    }


@app.get("/health")
async def health_check():
    """Check if Ollama is running"""
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
    """Main chat endpoint - Pakistan Fashion Chatbot"""
    
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
    try:
        from backend.Fashoin_chatbot.backend.tools import PAKISTAN_FESTIVALS
        return {
            "festivals": [
                {"key": key, "name": data["name"], "season": data["season"]}
                for key, data in PAKISTAN_FESTIVALS.items()
            ]
        }
    except ImportError:
        return {
            "status": "error",
            "message": "Festivals module not available"
        }


# ===== GlamourGPT Recommendation Endpoints =====
@app.get("/home")
def home():
    return {"message": "GlamourGPT Backend Running - Use /docs for full API documentation"}





@app.post("/recommend")
def recommend(body_type: str, weather: str, occasion: str):
    """
    Outfit recommendation based on body type, weather, and occasion
    """
    return recommend_outfit(body_type, weather, occasion)


@app.post("/fabric")
async def fabric_analysis(file: UploadFile = File(...)):
    """
    Fabric and color analysis from uploaded image
    """
    image_bytes = await file.read()
    return analyze_fabric(image_bytes)


@app.post("/tryon")
async def try_on(file: UploadFile = File(...)):
    """
    Virtual try-on using MediaPipe
    """
    image_bytes = await file.read()
    return virtual_tryon(image_bytes)

@app.post("/accessories")
def accessories(occasion: str):
    return {"accessories": suggest_accessories(occasion)}


# ===== Main Execution =====
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)