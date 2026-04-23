import os
import sys
import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Src folder ko path mein add karo
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from loader import GlamourBotLoader
from vectorstore import build_vectorstore, load_vectorstore
from rag_chain import build_rag_chain, chat
from voice import speech_to_text, text_to_speech

app = FastAPI(title="GlamourBot Fashion Assistant")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Transcript", "X-Response"],
)

# Global variables
rag_client = None
index      = None
docs       = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR   = os.path.join(BASE_DIR, "vector_db")
DATA_DIR = os.path.join(BASE_DIR, "data")


@app.on_event("startup")
async def startup():
    global rag_client, index, docs

    if os.path.exists(os.path.join(DB_DIR, "index.bin")):
        print("Loading existing vectorstore...")
        index, docs = load_vectorstore()
    else:
        print("Building vectorstore for first time...")
        loader = GlamourBotLoader()
        docs = loader.load_all(DATA_DIR)
        index, docs = build_vectorstore(docs)

    rag_client = build_rag_chain()
    print("GlamourBot is ready!")


# ── Models ──
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str


# ── Endpoints ──
@app.get("/")
def root():
    return {"message": "GlamourBot is running!"}

@app.get("/ui")
def ui():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.get("/config/image-keys")
def image_keys_config():
    return {
        "groq_api_key": os.getenv("GROQ_API_KEY", ""),
        "stability_api_key": os.getenv("STABILITY_API_KEY", os.getenv("Stabiliy_API_KEY", "")),
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    response = chat(rag_client, index, docs, request.message)
    return ChatResponse(response=response)

@app.post("/voice/input")
async def voice_input(audio: UploadFile = File(...)):
    try:
        audio_bytes = await audio.read()
        filename = audio.filename or "audio.webm"
        if not filename.endswith(('.webm', '.mp3', '.wav', '.m4a', '.ogg')):
            filename = "audio.webm"

        print(f"[VOICE] File: {filename}, Size: {len(audio_bytes)} bytes")

        # Speech to Text
        user_text = speech_to_text(audio_bytes, filename)
        print(f"[VOICE] User said: {user_text}")

        # RAG Answer
        answer = chat(rag_client, index, docs, user_text)
        print(f"[VOICE] Bot: {answer}")

        # Text to Speech
        audio_response = text_to_speech(answer)

        return Response(
            content=audio_response,
            media_type="audio/mpeg",
            headers={
                "X-Transcript": user_text,
                "X-Response": answer
            }
        )
    except Exception as e:
        import traceback
        print(f"[VOICE ERROR] {e}")
        traceback.print_exc()
        raise

@app.post("/rebuild")
async def rebuild_index():
    global index, docs
    loader = GlamourBotLoader()
    docs = loader.load_all(DATA_DIR)
    index, docs = build_vectorstore(docs)
    return {"message": "Index rebuilt!"}


# Static files
app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)