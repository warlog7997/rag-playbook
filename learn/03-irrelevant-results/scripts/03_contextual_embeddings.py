"""
Chapter 3, Script 3: Contextual embeddings — enrich chunks at index time.

The problem: sparse, instruction-heavy chunks embed poorly because they contain
few descriptive words. An intro section embeds better for topical queries because
it has a rich overview with many relevant terms.

The fix: for each chunk, ask Claude Haiku to generate a 1-2 sentence context
description — "what is this about and what question does it answer?" — and
PREPEND it to the chunk before embedding.

This makes the chunk self-describing, which dramatically improves retrieval
for queries that use different words than the chunk text itself.

Pipeline:
  1. Load all chunks from the BM25 index (same as the main index)
  2. For each chunk: ask Haiku for a context description
  3. Prepend description to chunk text
  4. Embed enriched text and store in a NEW ChromaDB collection: 'novadash_contextual'
  5. Compare plain vs contextual search on a few queries

Run: python 03_contextual_embeddings.py  (from the learn/ directory)
NOTE: This makes ~80 API calls to Claude Haiku (~$0.05 at current pricing).
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import load_bm25, get_embedding_model, ask_claude, vector_search
import chromadb

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
CHROMA_PATH = str(DATA_DIR / "chromadb")
CONTEXTUAL_COLLECTION = "novadash_contextual"

CONTEXT_SYSTEM = """You are a documentation indexing assistant. Your job is to write a
concise 1-2 sentence description of a documentation chunk that makes it easy to find
via search.

The description MUST:
1. State what topic or feature this section covers
2. State what question(s) this section answers for a user

Return ONLY the description — no JSON, no labels, no preamble. Just the 1-2 sentences."""


def generate_context_description(chunk_text: str, source: str, section: str) -> str:
    """Ask Claude Haiku to describe what a chunk is about and what question it answers."""
    user_prompt = f"""Documentation file: {source}
Section: {section}

Content:
{chunk_text[:600]}

Write a 1-2 sentence description of this section: what it covers and what user question it answers."""

    return ask_claude(
        system=CONTEXT_SYSTEM,
        user=user_prompt,
        model="claude-haiku-4-5-20251001",
    )


def ingest_contextual():
    """
    Build the contextual embeddings collection.
    For each chunk: generate context > prepend to chunk > embed > store.
    """
    print("=" * 65)
    print("  Building Contextual Embeddings Index")
    print("=" * 65)

    bm25, chunks = load_bm25()
    print(f"Loaded {len(chunks)} chunks from BM25 index.\n")

    model = get_embedding_model()
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Delete existing contextual collection if rebuilding
    try:
        client.delete_collection(CONTEXTUAL_COLLECTION)
        print(f"Deleted existing '{CONTEXTUAL_COLLECTION}' collection.")
    except Exception:
        pass

    collection = client.create_collection(CONTEXTUAL_COLLECTION)

    enriched_chunks = []
    total = len(chunks)

    for i, chunk in enumerate(chunks):
        print(f"[{i + 1}/{total}] {chunk['source']} > {chunk['section'][:40]}...", end="", flush=True)

        try:
            context_desc = generate_context_description(
                chunk["text"], chunk["source"], chunk["section"]
            )
            enriched_text = f"{context_desc}\n\n{chunk['text']}"
        except Exception as e:
            print(f" ERROR: {e} — using original")
            enriched_text = chunk["text"]
            context_desc = ""

        enriched_chunks.append({
            **chunk,
            "enriched_text": enriched_text,
            "context_description": context_desc,
        })

        print(f" done")

        # Small delay to avoid hitting rate limits
        if (i + 1) % 10 == 0:
            time.sleep(1)

    # Embed all enriched chunks
    print(f"\nEmbedding {len(enriched_chunks)} enriched chunks...")
    enriched_texts = [c["enriched_text"] for c in enriched_chunks]
    embeddings = model.encode(enriched_texts, show_progress_bar=True).tolist()

    collection.add(
        ids=[c["id"] for c in enriched_chunks],
        documents=enriched_texts,
        embeddings=embeddings,
        metadatas=[{
            "source": c["source"],
            "section": c["section"],
            "context_description": c["context_description"][:500],
        } for c in enriched_chunks],
    )

    print(f"\nContextual index built: {len(enriched_chunks)} chunks in '{CONTEXTUAL_COLLECTION}'")
    return collection


def contextual_search(query: str, top_k: int = 5) -> list[dict]:
    """Search the contextual embeddings collection."""
    model = get_embedding_model()
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(CONTEXTUAL_COLLECTION)

    query_embedding = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)

    hits = []
    for i, doc in enumerate(results["documents"][0]):
        hits.append({
            "text": doc,
            "source": results["metadatas"][0][i]["source"],
            "section": results["metadatas"][0][i]["section"],
            "context_description": results["metadatas"][0][i].get("context_description", ""),
            "score": 1 - results["distances"][0][i],
            "id": results["ids"][0][i],
        })
    return hits


def compare_search(query: str, top_k: int = 5):
    """
    Compare plain vector search vs contextual vector search for a query.
    Shows which approach returns the more relevant section at rank 1.
    """
    print(f"\nQuery: {query}")
    print(f"{'-' * 60}")

    plain_hits = vector_search(query, top_k=top_k)
    contextual_hits = contextual_search(query, top_k=top_k)

    print(f"\n{'Plain Embeddings':<40} {'Contextual Embeddings':<40}")
    print(f"{'-' * 40} {'-' * 40}")
    for i in range(min(top_k, len(plain_hits), len(contextual_hits))):
        p = plain_hits[i]
        c = contextual_hits[i]
        p_str = f"[{i+1}] {p['source'][:12]}>{p['section'][:22]}"
        c_str = f"[{i+1}] {c['source'][:12]}>{c['section'][:22]}"
        print(f"{p_str:<40} {c_str:<40}")

    # Show the context description of the #1 contextual result
    if contextual_hits:
        print(f"\nContextual #1 context description:")
        print(f"  {contextual_hits[0]['context_description']}")


# -----------------------------------------------------------------------------
# Main: build the index (if not already built) then compare
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Check if contextual collection already exists
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    existing = [c.name for c in client.list_collections()]

    if CONTEXTUAL_COLLECTION in existing:
        print(f"Contextual collection '{CONTEXTUAL_COLLECTION}' already exists.")
        rebuild = input("Rebuild it? (y/N): ").strip().lower()
        if rebuild == "y":
            ingest_contextual()
        else:
            print("Using existing contextual collection.")
    else:
        print("No contextual collection found — building it now...")
        ingest_contextual()

    # -- Compare on test queries
    print(f"\n\n{'=' * 65}")
    print("  Comparing Plain vs Contextual Search")
    print("=" * 65)

    test_queries = [
        "How do I set up two-factor authentication?",
        "What happens when I cancel my subscription?",
        "How does webhook signature verification work?",
        "What are the limits for free plan users?",
    ]

    for q in test_queries:
        compare_search(q, top_k=5)
        print()

    print("=" * 65)
    print("  Key Insight")
    print("=" * 65)
    print("""
Contextual embeddings fix the 'intro section dominates' problem by making
every chunk self-describing at index time.

Cost: One LLM call per chunk at ingestion (~$0.05 for 80 chunks).
      No extra cost at query time — the enriched text is already embedded.

Note from real-world results:
  Contextual embeddings show marginal improvement over hybrid search alone.
  The lesson: if retrieval is already good (hybrid), contextual embeddings
  add diminishing returns. Fix the retrieval first, then optimize embeddings.

See Chapter 6 (evaluation) for the full comparison including Recall@1 numbers.
""")
