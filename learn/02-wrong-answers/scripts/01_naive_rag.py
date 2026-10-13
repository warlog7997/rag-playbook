"""
Chapter 2, Script 1: Naive vector search on semantic gap queries.

Shows where naive RAG fails when user language doesn't match doc language.
The NovaDash docs intentionally use internal terminology (semantic gaps):
  - "account recovery" instead of "password reset"
  - "member offboarding" instead of "remove user"
  - "subscription termination" instead of "cancel"

Run: python 01_naive_rag.py  (from the learn/ directory)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import vector_search, format_results

# -----------------------------------------------------------------------------
# Test queries chosen to expose semantic gaps
# -----------------------------------------------------------------------------
TEST_QUERIES = [
    {
        "query": "How do I cancel my subscription?",
        "expected_source": "billing.md",
        "expected_section_keyword": "termination",
        "note": "Docs say 'subscription termination' — NOT 'cancel'",
    },
    {
        "query": "How do I remove a team member?",
        "expected_source": "user-management.md",
        "expected_section_keyword": "offboard",
        "note": "Docs say 'member offboarding' — NOT 'remove'",
    },
    {
        "query": "What happens when I forget my password?",
        "expected_source": "authentication.md",
        "expected_section_keyword": "recovery",
        "note": "Docs say 'account recovery via email verification token flow' — NOT 'password reset'",
    },
    {
        "query": "How many projects can I create on the free plan?",
        "expected_source": "projects.md",
        "expected_section_keyword": "limit",
        "note": "Direct language — should work fine",
    },
    {
        "query": "How to connect Slack to NovaDash?",
        "expected_source": "integrations.md",
        "expected_section_keyword": "Slack",
        "note": "Direct language — should work fine",
    },
]


def evaluate_hit(hits: list[dict], expected_source: str, expected_keyword: str) -> dict:
    """Check if the top result matches the expected source and section keyword."""
    if not hits:
        return {"top1_correct": False, "top1_source": "none", "rank_of_correct": -1}

    top1 = hits[0]
    top1_correct = (
        top1["source"] == expected_source
        and expected_keyword.lower() in top1["section"].lower()
    )

    # Find the rank of the correct answer (if it appears at all)
    rank_of_correct = -1
    for rank, hit in enumerate(hits, 1):
        if (hit["source"] == expected_source
                and expected_keyword.lower() in hit["section"].lower()):
            rank_of_correct = rank
            break

    return {
        "top1_correct": top1_correct,
        "top1_source": f"{top1['source']} > {top1['section']}",
        "rank_of_correct": rank_of_correct,
    }


# -----------------------------------------------------------------------------
# Run all queries
# -----------------------------------------------------------------------------
print("=" * 70)
print("  Chapter 2 — Naive Vector Search: Exposing Semantic Gaps")
print("=" * 70)

summary = []

for item in TEST_QUERIES:
    query = item["query"]
    print(f"\n{'-' * 70}")
    print(f"Query: {query}")
    print(f"Note:  {item['note']}")
    print(f"Expected: {item['expected_source']} (section containing '{item['expected_section_keyword']}')")

    hits = vector_search(query, top_k=5)

    print("\nTop 3 results:")
    for i, hit in enumerate(hits[:3], 1):
        marker = "OK" if (
            hit["source"] == item["expected_source"]
            and item["expected_section_keyword"].lower() in hit["section"].lower()
        ) else "FAIL"
        print(f"  [{i}] {marker} {hit['source']} > {hit['section']}  (score: {hit['score']:.4f})")

    eval_result = evaluate_hit(hits, item["expected_source"], item["expected_section_keyword"])
    summary.append({
        "query": query[:45] + "..." if len(query) > 45 else query,
        "correct_at_1": eval_result["top1_correct"],
        "top_1_returned": eval_result["top1_source"],
        "correct_at_rank": eval_result["rank_of_correct"],
    })

# -----------------------------------------------------------------------------
# Summary table
# -----------------------------------------------------------------------------
print(f"\n\n{'=' * 70}")
print("  SUMMARY: Naive Vector Search Performance")
print("=" * 70)
print(f"\n{'Query':<47} {'Top-1 Correct':^13} {'Correct at Rank'}")
print(f"{'-' * 47} {'-' * 13} {'-' * 15}")

correct_count = 0
for s in summary:
    status = "  OK  CORRECT" if s["correct_at_1"] else "  FAIL  WRONG  "
    rank_str = f"rank {s['correct_at_rank']}" if s["correct_at_rank"] > 0 else "not found"
    print(f"{s['query']:<47} {status:^13} {rank_str}")
    if s["correct_at_1"]:
        correct_count += 1

recall_at_1 = correct_count / len(summary)
print(f"\n{'-' * 70}")
print(f"Recall@1: {correct_count}/{len(summary)} = {recall_at_1:.2f}")
print(f"\nConclusion: Naive vector search fails on semantic gaps.")
print(f"Run 02_bm25_search.py to see where BM25 helps — and where it doesn't.\n")
