# ZaibunBot - Pakistan Fashion AI Chatbot 🇵🇰👗

## Quick Setup (3 Steps)

### Step 1: Install Python Dependencies
```bash
cd pakistan-fashion-bot
pip install -r requirements.txt
```

### Step 2: Make sure Ollama is running with your model
```bash
# Start Ollama service (if not already running)
ollama serve

# Verify your model is available (in another terminal)
ollama list
# You should see: qwen2.5:0.5b
```

### Step 3: Start the Backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Step 4: Open the Frontend
Open `frontend/index.html` in your browser (Chrome or Edge recommended for voice support)

---

## Architecture

```
User Input
    │
    ├── Voice Input (🎤) ──► Web Speech API (STT) ──► Text
    │
    └── Text Input ──────────────────────────────────► Text
                                                         │
                                              FastAPI Backend (port 8000)
                                                         │
                                              Intent Detection (Agent)
                                                         │
                                    ┌────────────────────┴────────────────────┐
                                    │                                         │
                            Tool Selected                              General Query
                         (Festival/Designer/Trend)                           │
                                    │                                         │
                            Knowledge Base                           Ollama qwen2.5:0.5b
                                    │                                         │
                                    └────────────────► Context + Query ───────┘
                                                               │
                                                    Ollama qwen2.5:0.5b
                                                               │
                                                          Response Text
                                                               │
                               ┌───────────────────────────────┤
                               │                               │
                        Voice Input?                    Text Input?
                               │                               │
                     TTS (Speak Response)            Display in Chat
```

## Features

| Feature | Details |
|---------|---------|
| 🎤 Voice Input | Click mic button, speak your question |
| 🔊 Voice Output | Auto-speaks when voice input used; manual 🔊 button for text |
| 🤖 Local AI | Uses your qwen2.5:0.5b model via Ollama |
| 🎊 Festival Knowledge | Eid, Basant, Independence Day, Weddings, Navratri, Christmas |
| 👗 Fashion Advice | Regional styles, designers, trends, fabric guide |
| 🌐 REST API | Full API at http://localhost:8000/docs |

## API Endpoints

- `POST /chat` — Send a message
- `GET /health` — Check Ollama connection  
- `GET /festivals` — List all Pakistani festivals
- `DELETE /chat/{session_id}` — Clear chat history

## Troubleshooting

**"Cannot connect to server"**
→ Run: `cd backend && uvicorn main:app --reload`

**"Cannot connect to Ollama"**
→ Run: `ollama serve` in a terminal

**Voice not working**
→ Use Chrome or Edge browser (Firefox has limited Web Speech API support)
→ Allow microphone permission when prompted

**Model too slow**
→ qwen2.5:0.5b is small and fast. Should respond in 2-10 seconds.
