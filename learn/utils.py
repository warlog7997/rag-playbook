"""Shared utilities for all RAG examples."""
import os
import pickle
import keyring
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer
import anthropic

DATA_DIR = Path(__file__).parent.parent / "data"
CHROMA_PATH = str(DATA_DIR / "chromadb")
BM25_PATH = DATA_DIR / "bm25_index.pkl"
COLLECTION_NAME = "novadash_docs"

# Module-level singletons — loaded lazily to keep startup fast
_model = None
_collection = None
_bm25_data = None


def get_embedding_model():
    """Load the sentence-transformer model (cached after first call)."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def load_chroma():
    """Connect to ChromaDB and return the collection (cached after first call)."""
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = client.get_collection(COLLECTION_NAME)
    return _collection


def load_bm25():
    """Load the BM25 index from disk (cached after first call)."""
    global _bm25_data
    if _bm25_data is None:
        if not BM25_PATH.exists():
            raise FileNotFoundError(
                f"BM25 index not found at {BM25_PATH}. Run 'python learn/ingest.py' first."
            )
        with open(BM25_PATH, "rb") as f:
            _bm25_data = pickle.load(f)
    return _bm25_data["bm25"], _bm25_data["chunks"]


def vector_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Search ChromaDB by semantic (vector) similarity.

    Returns a list of dicts with keys:
      text, source, section, score, id
    """
    model = get_embedding_model()
    collection = load_chroma()

    query_embedding = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)

    hits = []
    for i, doc in enumerate(results["documents"][0]):
        hits.append({
            "text": doc,
            "source": results["metadatas"][0][i]["source"],
            "section": results["metadatas"][0][i]["section"],
            # ChromaDB returns L2 distance; convert to 0-1 similarity (approximate)
            "score": 1 - results["distances"][0][i],
            "id": results["ids"][0][i],
        })
    return hits


def bm25_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Search using BM25 keyword matching.

    Returns a list of dicts with keys:
      text, source, section, score, id
    """
    bm25, chunks = load_bm25()
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    hits = []
    for idx in top_indices:
        hits.append({
            "text": chunks[idx]["text"],
            "source": chunks[idx]["source"],
            "section": chunks[idx]["section"],
            "score": float(scores[idx]),
            "id": chunks[idx]["id"],
        })
    return hits


def hybrid_search(query: str, top_k: int = 5, fetch_k: int = 10) -> list[dict]:
    """
    Hybrid search: Vector + BM25 combined with Reciprocal Rank Fusion (RRF).

    RRF formula: score(doc) = sum over each ranking of 1 / (rank + k)
    where k=60 is the standard constant from the original RRF paper.

    Returns top_k results sorted by RRF score (descending).
    """
    vector_hits = vector_search(query, top_k=fetch_k)
    bm25_hits = bm25_search(query, top_k=fetch_k)

    rrf_scores = {}
    all_hits = {}

    for rank, hit in enumerate(vector_hits):
        rrf_scores[hit["id"]] = rrf_scores.get(hit["id"], 0) + 1 / (rank + 60)
        all_hits[hit["id"]] = hit

    for rank, hit in enumerate(bm25_hits):
        rrf_scores[hit["id"]] = rrf_scores.get(hit["id"], 0) + 1 / (rank + 60)
        all_hits[hit["id"]] = hit

    sorted_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)[:top_k]

    results = []
    for id_ in sorted_ids:
        hit = all_hits[id_].copy()
        hit["rrf_score"] = rrf_scores[id_]
        results.append(hit)
    return results


def ask_claude(system: str, user: str, model: str = "claude-haiku-4-5-20251001") -> str:
    """
    Call Claude with a system + user prompt. Returns response text.

    Uses keyring to retrieve the API key — set it once with:
        import keyring
        keyring.set_password("Anthorpic", "API_KEY", "your-key-here")
    """
    api_key = keyring.get_password("Anthorpic", "API_KEY")
    if not api_key:
        raise ValueError(
            "Anthropic API key not found. Set it with:\n"
            "  import keyring\n"
            "  keyring.set_password('Anthorpic', 'API_KEY', 'your-key-here')"
        )
    client = anthropic.Anthropic(api_key=api_key.strip())
    for attempt in range(3):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return response.content[0].text
        except Exception as e:
            if attempt == 2:
                raise
            import time
            time.sleep(2 ** attempt)


def format_results(hits: list[dict], title: str = "Results"):
    """Pretty print retrieved chunks with scores and source info."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    for i, hit in enumerate(hits, 1):
        score = hit.get("rrf_score") or hit.get("score", 0)
        print(f"\n[{i}] {hit['source']} > {hit['section']}")
        print(f"    Score: {score:.4f}")
        print(f"    Preview: {hit['text'][:150].strip()}...")
    print()
