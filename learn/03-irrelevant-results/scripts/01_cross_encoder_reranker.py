"""
Chapter 3, Script 1: Cross-encoder reranker.

Pipeline:
  1. Hybrid search > 15 candidates (wide net, high recall)
  2. Cross-encoder scores each (query, chunk) pair
  3. Re-sort by cross-encoder score

Model: cross-encoder/ms-marco-MiniLM-L-12-v2
  - Trained on MS MARCO web search relevance dataset
  - Runs locally (no API call) — fast and free
  - Limitation: trained on web queries, may not fully understand SaaS docs

Run: python 01_cross_encoder_reranker.py  (from the learn/ directory)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import hybrid_search
from sentence_transformers import CrossEncoder

# -----------------------------------------------------------------------------
# Load the cross-encoder model (downloaded on first run, ~67 MB)
# -----------------------------------------------------------------------------
print("Loading cross-encoder model (ms-marco-MiniLM-L-12-v2)...")
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-12-v2")
print("Model loaded.\n")

# -----------------------------------------------------------------------------
# Test queries — chosen to show reranking's impact on section selection
# -----------------------------------------------------------------------------
TEST_QUERIES = [
    {
        "query": "How do I set up two-factor authentication?",
        "expected_source": "authentication.md",
        "expected_section": "Two-Factor Authentication",
        "note": "Intro section will rank #1 without reranker; 2FA section should be #1 after",
    },
    {
        "query": "What webhook events does NovaDash support?",
        "expected_source": "notifications.md",
        "expected_section": "Webhook",
        "note": "Notifications intro mentions webhooks; specific webhook section has event types",
    },
    {
        "query": "How do I import users from a CSV file?",
        "expected_source": "user-management.md",
        "expected_section": "Bulk User Import",
        "note": "User management intro is broad; CSV import section is highly specific",
    },
]

FETCH_K = 15  # Fetch this many candidates before reranking


def rerank_with_cross_encoder(query: str, hits: list[dict]) -> list[dict]:
    """
    Score each (query, chunk) pair using the cross-encoder.
    Returns hits sorted by cross-encoder score (descending).
    """
    pairs = [(query, hit["text"]) for hit in hits]
    scores = reranker.predict(pairs)

    reranked = []
    for hit, score in zip(hits, scores):
        reranked.append({**hit, "ce_score": float(score)})

    reranked.sort(key=lambda x: x["ce_score"], reverse=True)
    return reranked


# -----------------------------------------------------------------------------
# Run each query: show before and after reranking
# -----------------------------------------------------------------------------
for item in TEST_QUERIES:
    query = item["query"]
    print("=" * 70)
    print(f"Query: {query}")
    print(f"Note:  {item['note']}")
    print("=" * 70)

    # Stage 1: Hybrid retrieval (wide net)
    candidates = hybrid_search(query, top_k=FETCH_K, fetch_k=FETCH_K)
    print(f"\nStage 1 — Hybrid retrieval: {len(candidates)} candidates\n")

    # Stage 2: Cross-encoder reranking
    reranked = rerank_with_cross_encoder(query, candidates)

    # Show top 5 before reranking
    print("BEFORE reranking (hybrid order):")
    for i, hit in enumerate(candidates[:5], 1):
        is_target = (
            item["expected_source"] in hit["source"]
            and item["expected_section"].lower() in hit["section"].lower()
        )
        marker = "★ TARGET" if is_target else "       "
        print(f"  [{i}] {marker} {hit['source']} > {hit['section']}")

    # Show top 5 after reranking
    print("\nAFTER cross-encoder reranking:")
    for i, hit in enumerate(reranked[:5], 1):
        is_target = (
            item["expected_source"] in hit["source"]
            and item["expected_section"].lower() in hit["section"].lower()
        )
        marker = "★ TARGET" if is_target else "       "
        print(f"  [{i}] {marker} {hit['source']} > {hit['section']}  "
              f"(CE score: {hit['ce_score']:.3f})")

    # Did reranking move the target to #1?
    before_rank = next(
        (i + 1 for i, h in enumerate(candidates)
         if item["expected_source"] in h["source"]
         and item["expected_section"].lower() in h["section"].lower()),
        -1
    )
    after_rank = next(
        (i + 1 for i, h in enumerate(reranked)
         if item["expected_source"] in h["source"]
         and item["expected_section"].lower() in h["section"].lower()),
        -1
    )
    print(f"\n  Target section rank: {before_rank} > {after_rank} after reranking")
    print()

# -----------------------------------------------------------------------------
# Note on cross-encoder limitations
# -----------------------------------------------------------------------------
print("=" * 70)
print("  Cross-Encoder Notes")
print("=" * 70)
print("""
Strengths:
  OK Runs locally — no API cost, no latency from external calls
  OK Fast on CPU for small candidate sets (15 chunks ≈ 750ms)
  OK Better precision than bi-encoder retrieval alone

Limitations:
  FAIL Trained on MS MARCO (web search queries) — may misunderstand SaaS
    domain terminology like "member offboarding" or "identity provider binding"
  FAIL Can't be easily prompted to prefer certain answer styles
  FAIL Scores are not calibrated probabilities — use for ranking only

Next: Run 02_llm_reranker.py to see an LLM-based approach that understands
the domain better, at the cost of API calls.
""")
