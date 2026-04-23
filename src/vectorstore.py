import os
import json
import pickle
import numpy as np
import hnswlib
from sentence_transformers import SentenceTransformer

# Paths
BASE_DIR   = os.path.join(os.path.dirname(__file__), "..")
DB_DIR     = os.path.join(BASE_DIR, "vector_db")
INDEX_FILE = os.path.join(DB_DIR, "index.bin")
DOCS_FILE  = os.path.join(DB_DIR, "docs.pkl")

MODEL_NAME = "all-MiniLM-L6-v2"
DIM        = 384  # all-MiniLM-L6-v2 ka dimension


def get_model():
    print("Loading embedding model...")
    return SentenceTransformer(MODEL_NAME)


def build_vectorstore(docs: list[dict]):
    """Pehli baar vectorstore banao."""
    print("\nBuilding vectorstore...")

    os.makedirs(DB_DIR, exist_ok=True)

    model = get_model()

    # Embeddings banao
    contents = [d["content"] for d in docs]
    print(f"Creating embeddings for {len(contents)} documents...")
    embeddings = model.encode(contents, show_progress_bar=True, batch_size=64)
    embeddings = np.array(embeddings, dtype=np.float32)

    # HNSW Index banao
    index = hnswlib.Index(space="cosine", dim=DIM)
    index.init_index(max_elements=len(docs), ef_construction=200, M=16)
    index.add_items(embeddings, list(range(len(docs))))
    index.set_ef(50)

    # Save karo
    index.save_index(INDEX_FILE)
    with open(DOCS_FILE, "wb") as f:
        pickle.dump(docs, f)

    print(f"[DONE] Vectorstore saved! Total: {len(docs)} documents")
    return index, docs


def load_vectorstore():
    """Existing vectorstore load karo."""
    if not os.path.exists(INDEX_FILE):
        raise FileNotFoundError("Vectorstore nahi mila! Pehle build_vectorstore() chalao.")

    with open(DOCS_FILE, "rb") as f:
        docs = pickle.load(f)

    index = hnswlib.Index(space="cosine", dim=DIM)
    index.load_index(INDEX_FILE, max_elements=len(docs))
    index.set_ef(50)

    print(f"[OK] Vectorstore loaded. Total docs: {len(docs)}")
    return index, docs


def search(index, docs: list[dict], query: str, n_results: int = 5) -> list[str]:
    """Query ke liye relevant documents dhundo."""
    model = get_model()
    query_embedding = model.encode([query], convert_to_numpy=True).astype(np.float32)

    labels, _ = index.knn_query(query_embedding, k=n_results)

    results = [docs[i]["content"] for i in labels[0]]
    return results


# Test
if __name__ == "__main__":
    from loader import GlamourBotLoader

    loader = GlamourBotLoader()
    docs = loader.load_all(r"C:\Users\user\Desktop\GlamourBot\data")

    index, docs = build_vectorstore(docs)

    print("\n--- Test Search ---")
    query = "What should I wear to a Pakistani wedding?"
    results = search(index, docs, query)

    print(f"Query: {query}")
    for i, r in enumerate(results):
        print(f"\n[{i+1}] {r[:200].encode("ascii", "ignore").decode()}...")