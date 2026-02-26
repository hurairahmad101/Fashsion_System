"""
Agentic System for Pakistan Fashion Chatbot
Uses Ollama (qwen2.5:0.5b) as the local LLM
"""

import requests
import json
import re
from backend.Fashoin_chatbot.backend.tools import (
    get_festival_fashion,
    get_designer_info,
    get_fashion_trends,
    get_all_festivals,
    PAKISTAN_FESTIVALS
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:0.5b"

SYSTEM_PROMPT = """You are ZaibunBot, an expert AI assistant specializing in Pakistani fashion, clothing, and cultural festivals. 

Your expertise includes:
- Traditional Pakistani clothing (shalwar kameez, gharara, sherwani, etc.)
- Pakistani festivals and their fashion traditions (Eid, Basant, weddings, Independence Day)
- Pakistani fashion designers and brands
- Regional fashion styles (Lahore, Karachi, Sindh, Balochistan, KPK)
- Fabric types popular in Pakistan (lawn, chiffon, khaddar, silk, cotton)
- Embroidery styles (zardozi, gota, tarkashi, mirror work, thread work)
- Current fashion trends in Pakistan

Always respond in a warm, helpful, and culturally aware manner. 
Keep responses concise but informative.
If tool data is provided, use it to give accurate answers.
Always answer in the same language the user asks (Urdu or English)."""


def detect_intent(query: str) -> dict:
    """
    Simple intent detection to route to appropriate tools
    Returns: {intent, params}
    """
    query_lower = query.lower()
    
    # Festival keywords
    festival_keywords = {
        "eid ul fitr": ["eid ul fitr", "eid fitr", "chand raat", "ramadan eid", "meethi eid"],
        "eid ul adha": ["eid ul adha", "bakra eid", "qurbani", "eid adha"],
        "basant": ["basant", "kite festival", "spring festival", "patang"],
        "independence day": ["independence day", "14 august", "azaadi", "14th august", "jashn e azaadi"],
        "wedding season": ["wedding", "shaadi", "mehndi", "barat", "valima", "nikah", "shadi"],
        "navratri": ["navratri", "garba", "dandiya"],
        "christmas": ["christmas", "x-mas", "december 25"]
    }
    
    for festival, keywords in festival_keywords.items():
        for kw in keywords:
            if kw in query_lower:
                return {"intent": "festival_fashion", "festival": festival}
    
    # Designer keywords
    if any(word in query_lower for word in ["designer", "brand", "bridal designer", "fashion house", "who makes", "khaadi", "gul ahmed", "maria b", "hsy"]):
        category = None
        if "bridal" in query_lower:
            category = "bridal"
        elif "lawn" in query_lower or "pret" in query_lower:
            category = "lawn_pret"
        elif "men" in query_lower:
            category = "menswear"
        elif "luxury" in query_lower:
            category = "luxury"
        return {"intent": "designers", "category": category}
    
    # Trends
    if any(word in query_lower for word in ["trend", "latest", "current fashion", "what's in", "whats in", "popular now", "new fashion"]):
        return {"intent": "trends"}
    
    # List all festivals
    if any(word in query_lower for word in ["all festivals", "list festival", "which festivals", "festivals in pakistan", "what festivals"]):
        return {"intent": "all_festivals"}
    
    # General fashion query
    return {"intent": "general", "query": query}


def get_tool_context(intent_data: dict) -> str:
    """Get relevant context from tools based on intent"""
    intent = intent_data.get("intent")
    
    if intent == "festival_fashion":
        result = get_festival_fashion(intent_data.get("festival", ""))
        return result if result else ""
    
    elif intent == "designers":
        return get_designer_info(intent_data.get("category"))
    
    elif intent == "trends":
        return get_fashion_trends()
    
    elif intent == "all_festivals":
        return get_all_festivals()
    
    return ""


def query_ollama(prompt: str, system: str = "") -> str:
    """Send query to local Ollama model"""
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 500
            }
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "I couldn't generate a response. Please try again.")
    
    except requests.exceptions.ConnectionError:
        return "❌ Error: Cannot connect to Ollama. Please make sure Ollama is running with: ollama serve"
    except requests.exceptions.Timeout:
        return "❌ Error: Request timed out. The model is taking too long to respond."
    except Exception as e:
        return f"❌ Error: {str(e)}"


def run_agent(user_query: str, conversation_history: list = None) -> str:
    """
    Main agentic function:
    1. Detects intent
    2. Fetches tool context
    3. Sends to LLM with context
    4. Returns response
    """
    
    # Step 1: Detect intent and get tool data
    intent_data = detect_intent(user_query)
    tool_context = get_tool_context(intent_data)
    
    # Step 2: Build prompt with context
    if tool_context:
        prompt = f"""User Question: {user_query}

Relevant Information from Knowledge Base:
{tool_context}

Based on the above information, please provide a helpful, conversational response about Pakistani fashion for the user's question. 
Be warm, specific, and culturally accurate. Keep it concise (2-4 sentences or a short list)."""
    else:
        # Build conversation history context
        history_text = ""
        if conversation_history:
            for msg in conversation_history[-4:]:  # Last 4 messages for context
                role = "User" if msg["role"] == "user" else "Assistant"
                history_text += f"{role}: {msg['content']}\n"
        
        prompt = f"""{history_text}User: {user_query}

Please answer this question about Pakistani fashion, clothing, culture, or festivals. 
Be helpful, accurate, and culturally sensitive."""
    
    # Step 3: Get LLM response
    response = query_ollama(prompt, SYSTEM_PROMPT)
    
    return response


if __name__ == "__main__":
    # Test the agent
    print("Testing Pakistan Fashion Agent...")
    print("-" * 50)
    
    test_queries = [
        "What should I wear for Eid ul Fitr?",
        "Tell me about Basant festival fashion",
        "Who are the top bridal designers in Pakistan?"
    ]
    
    for query in test_queries:
        print(f"\nQ: {query}")
        response = run_agent(query)
        print(f"A: {response}")
        print("-" * 50)
