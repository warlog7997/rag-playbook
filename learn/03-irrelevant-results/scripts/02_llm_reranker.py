"""
Chapter 3, Script 2: LLM-as-reranker using Claude Haiku.

Instead of a cross-encoder trained on web queries, we ask Claude Haiku to
score each (query, chunk) pair for relevance. Claude understands SaaS domain
terminology and can be prompted to prefer chunks with actionable instructions.

Pipeline:
  1. Hybrid search > 15 candidates
  2. For each candidate: ask Claude Haiku for a relevance score (1-10)
  3. Parse JSON response: {"score": 8, "reason": "..."}
  4. Re-sort by score and compare with cross-encoder results

Cost: ~15 Claude Haiku API calls per query (~$0.005 per query at current pricing)
Speed: ~3-5 seconds per query (parallel calls would be faster)

Run: python 02_llm_reranker.py  (from the learn/ directory)
"""
import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import hybrid_search, ask_claude
from sentence_transformers import CrossEncoder

# Test queries (same as script 1)
TEST_QUERIES = [
    {
        "query": "How do I set up two-factor authentication?",
        "expected_source": "authentication.md",
        "expected_section": "Two-Factor Authentication",
    },
    {
        "query": "What webhook events does NovaDash support?",
        "expected_source": "notifications.md",
        "expected_section": "Webhook",
    },
    {
        "query": "How do I import users from a CSV file?",
        "expected_source": "user-management.md",
        "expected_section": "Bulk User Import",
    },
]

FETCH_K = 15

RERANK_SYSTEM = """You are a relevance scoring assistant for a documentation search system.
You will receive a user query and a documentation chunk. Score how relevant the chunk is
to answering the query.

Return ONLY a JSON object in this exact format:
{"score": <integer 1-10>, "reason": "<one sentence explanation>"}

Scoring guide:
  10 = Chunk directly and completely answers the query with specific details or steps
   8 = Chunk is highly relevant and contains most of the needed information
   6 = Chunk is related to the topic but doesn't fully answer the query
   4 = Chunk is from the right domain but only tangentially related
   2 = Chunk mentions the topic in passing but is not useful for this query
   1 = Chunk is unrelated to the query"""


def score_chunk_with_llm(query: str, chunk_text: str) -> dict:
    """
    Ask Claude Haiku to score a single (query, chunk) pair.
    Returns {"score": int, "reason": str} or falls back to {"score": 5, "reason": "parse error"}
    """
    user_prompt = f"""Query: {query}

Documentation chunk:
{chunk_text[:800]}

Score this chunk's relevance to the query."""

    response = ask_claude(
        system=RERANK_SYSTEM,
        user=user_prompt,
        model="claude-haiku-4-5-20251001",
    )

    # Parse the JSON response
    try:
        # Handle cases where Claude wraps the JSON in ```json ... ```
        clean = re.sub(r"```json\s*|\s*```", "", response).strip()
        result = json.loads(clean)
        return {"score": int(result["score"]), "reason": result.get("reason", "")}
    except (json.JSONDecodeError, KeyError, ValueError):
        # If parsing fails, extract score with regex as fallback
        match = re.search(r'"score"\s*:\s*(\d+)', response)
        score = int(match.group(1)) if match else 5
        return {"score": score, "reason": "parse fallback"}


def rerank_with_llm(query: str, hits: list[dict]) -> list[dict]:
    """Score all candidates with Claude Haiku and re-sort."""
    print(f"  Scoring {len(hits)} chunks with Claude Haiku...")
    reranked = []
    for i, hit in enumerate(hits):
        print(f"    [{i + 1}/{len(hits)}] {hit['source']} > {hit['section'][:40]}", end="", flush=True)
        score_result = score_chunk_with_llm(query, hit["text"])
        print(f" > score: {score_result['score']}")
        reranked.append({
            **hit,
            "llm_score": score_result["score"],
            "llm_reason": score_result["reason"],
        })

    reranked.sort(key=lambda x: x["llm_score"], reverse=True)
    return reranked


def rerank_with_cross_encoder(query: str, hits: list[dict]) -> list[dict]:
    """Cross-encoder reranking for comparison (same as script 1)."""
    reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-12-v2")
    pairs = [(query, hit["text"]) for hit in hits]
    scores = reranker.predict(pairs)
    reranked = [{**hit, "ce_score": float(score)} for hit, score in zip(hits, scores)]
    reranked.sort(key=lambda x: x["ce_score"], reverse=True)
    return reranked


# -----------------------------------------------------------------------------
# Run comparison
# -----------------------------------------------------------------------------
print("Loading cross-encoder for comparison...")
# Pre-load once (used in rerank_with_cross_encoder)
_ce_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-12-v2")

for item in TEST_QUERIES:
    query = item["query"]
    print(f"\n{'=' * 70}")
    print(f"Query: {query}")
    print("=" * 70)

    candidates = hybrid_search(query, top_k=FETCH_K, fetch_k=FETCH_K)
    print(f"Retrieved {len(candidates)} candidates via hybrid search.\n")

    # LLM reranking
    llm_reranked = rerank_with_llm(query, candidates)

    # Cross-encoder reranking (for comparison, no extra API call needed)
    pairs = [(query, hit["text"]) for hit in candidates]
    ce_scores = _ce_model.predict(pairs)
    ce_reranked = sorted(
        [{**h, "ce_score": float(s)} for h, s in zip(candidates, ce_scores)],
        key=lambda x: x["ce_score"], reverse=True
    )

    # Print top 5 from each approach
    print(f"\n{'Hybrid (no rerank)':<35} {'Cross-Encoder':<35} {'LLM Reranker':<35}")
    print(f"{'-' * 35} {'-' * 35} {'-' * 35}")
    for i in range(min(5, len(candidates))):
        h = candidates[i]
        c = ce_reranked[i]
        l = llm_reranked[i]

        def fmt(hit):
            is_target = (
                item["expected_source"] in hit["source"]
                and item["expected_section"].lower() in hit["section"].lower()
            )
            prefix = "★ " if is_target else "  "
            return f"[{i+1}]{prefix}{hit['source'][:12]}>{hit['section'][:18]}"

        print(f"{fmt(h):<35} {fmt(c):<35} {fmt(l):<35}")

    # Show LLM scores with reasons for top 3
    print("\nLLM Reranker — Top 3 with reasons:")
    for i, hit in enumerate(llm_reranked[:3], 1):
        print(f"  [{i}] {hit['source']} > {hit['section']}")
        print(f"       Score: {hit['llm_score']}/10 — {hit['llm_reason']}")

    # Rank comparison
    def get_rank(hits_list, source, section_keyword):
        for rank, h in enumerate(hits_list, 1):
            if source in h["source"] and section_keyword.lower() in h["section"].lower():
                return rank
        return -1

    before = get_rank(candidates, item["expected_source"], item["expected_section"])
    ce_rank = get_rank(ce_reranked, item["expected_source"], item["expected_section"])
    llm_rank = get_rank(llm_reranked, item["expected_source"], item["expected_section"])
    print(f"\n  Target section rank: Hybrid={before}, CrossEncoder={ce_rank}, LLM={llm_rank}")

print(f"\n\n{'=' * 70}")
print("  LLM Reranker vs Cross-Encoder: Summary")
print("=" * 70)
print("""
LLM Reranker strengths:
  OK Understands domain-specific language ("subscription termination", "offboarding")
  OK Can reason about what makes a good answer (steps vs overview)
  OK Provides human-readable explanations for why each chunk was scored

LLM Reranker weaknesses:
  FAIL ~15 API calls per query — adds 3-5 seconds latency
  FAIL More expensive than a local cross-encoder
  FAIL Non-deterministic — scores can vary slightly between runs

Recommendation:
  Use cross-encoder for high-traffic, latency-sensitive queries.
  Use LLM reranker for high-value queries where accuracy matters more than speed,
  or when the domain vocabulary is very specialized.

Next: Run 03_contextual_embeddings.py to see a third approach that fixes the
problem at index time rather than at query time.
""")
