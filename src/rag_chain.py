import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

PROMPT_TEMPLATE = """You are GlamourBot — a smart, friendly AI fashion assistant.

You specialize in:
- Outfit recommendations based on body type, skin tone, and occasion
- Pakistani and Western fashion advice
- Event styling (weddings, mehndi, baraat, casual, formal)
- Brand suggestions and accessory matching

Use the context below to answer the question.
If context is not enough, use your own fashion knowledge.
Detect the language of the user's question and always respond in the same language. If user writes in Roman Urdu or Urdu, respond in Roman Urdu. If user writes in English, respond in English.
Always be warm, helpful, and give specific fashion advice.

Context:
{context}

Question: {question}

GlamourBot Answer:"""


def build_rag_chain():
    client = Groq(api_key=os.getenv("GROQ_API_KEY"), timeout=60.0)
    return client


def chat(client, index, docs, user_message: str) -> str:
    from vectorstore import search

    # 1. Relevant chunks search karo
    chunks = search(index, docs, user_message, n_results=5)
    context = "\n\n".join(chunks)

    # 2. Prompt banao
    prompt = PROMPT_TEMPLATE.format(
        context=context,
        question=user_message
    )

    # 3. Groq API call
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1024
    )

    return response.choices[0].message.content


# Test
if __name__ == "__main__":
    from loader import GlamourBotLoader
    from vectorstore import load_vectorstore

    index, docs = load_vectorstore()
    client = build_rag_chain()

    questions = [
        "What should I wear to a Pakistani wedding?",
        "I have a pear body type, what outfits suit me?",
        "What colors are best for mehndi function?"
    ]

    for q in questions:
        print(f"\nQ: {q}")
        answer = chat(client, index, docs, q)
        print(f"A: {answer}")
        print("-" * 50)