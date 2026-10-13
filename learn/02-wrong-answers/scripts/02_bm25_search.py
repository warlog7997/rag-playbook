"""
Chapter 2, Script 2: BM25 keyword search on the same semantic gap queries.

BM25 (Best Matching 25) is a classical IR algorithm that scores based on
keyword overlap — how often query terms appear in each document, weighted
by inverse document frequency (rare terms score higher).

Where BM25 WINS vs naive:
  - When the user uses exact words from the docs ("termination", "offboarding")
  - When there's a strong keyword signal

Where BM25 FAILS:
  - When user paraphrases ("stop paying" vs "termination")
  - When user uses synonyms not present in the docs

Run: python 02_bm25_search.py  (from the learn/ directory)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import bm25_search

# Same queries as Script 1
TEST_QUERIES = [
    {
        "query": "How do I cancel my subscription?",
        "expected_source": "billing.md",
        "expected_section_keyword": "termination",
        "note": "User says 'cancel' — docs say 'termination'. Does BM25 find 'cancel' anywhere?",
    },
    {
        "query": "How do I remove a team member?",
        "expected_source": "user-management.md",
        "expected_section_keyword": "offboard",
        "note": "User says 'remove' — docs say 'offboarding'. BM25 looks for exact words.",
    },
    {
        "query": "What happens when I forget my password?",
        "expected_source": "authentication.md",
        "expected_section_keyword": "recovery",
        "note": "User says 'forget password' — docs say 'account recovery'. Does 'password' appear?",
    },
    {
        "query": "How many projects can I create on the free plan?",
        "expected_source": "projects.md",
        "expected_section_keyword": "limit",
        "note": "Direct language — 'projects', 'free plan' are exact doc terms.",
    },
    {
        "query": "How to connect Slack to NovaDash?",
        "expected_source": "integrations.md",
        "expected_section_keyword": "Slack",
        "note": "Direct language — 'Slack' is exact. Should score perfectly.",
    },
]

# Also test some EXTRA queries to show where BM25 fails
EXTRA_PARAPHRASE_QUERIES = [
    {
        "query": "stop paying for NovaDash",
        "expected_source": "billing.md",
        "expected_section_keyword": "termination",
        "note": "Pure paraphrase — no doc words present. BM25 should fail.",
    },
    {
        "query": "how to end my account",
        "expected_source": "billing.md",
        "expected_section_keyword": "termination",
        "note": "Paraphrase with no keyword match. BM25 should fail.",
    },
]


def evaluate_hit(hits, expected_source, expected_keyword):
    """Return whether the correct answer is ranked #1 and what rank it appears at."""
    if not hits:
        return False, "none", -1

    top1 = hits[0]
    top1_correct = (
        top1["source"] == expected_source
        and expected_keyword.lower() in top1["section"].lower()
    )

    rank_of_correct = -1
    for rank, hit in enumerate(hits, 1):
        if (hit["source"] == expected_source
                and expected_keyword.lower() in hit["section"].lower()):
            rank_of_correct = rank
            break

    return top1_correct, f"{top1['source']} > {top1['section']}", rank_of_correct


print("=" * 70)
print("  Chapter 2 — BM25 Keyword Search")
print("=" * 70)

summary = []

for item in TEST_QUERIES:
    query = item["query"]
    print(f"\n{'-' * 70}")
    print(f"Query: {query}")
    print(f"Note:  {item['note']}")

    hits = bm25_search(query, top_k=5)

    print("\nTop 3 results:")
    for i, hit in enumerate(hits[:3], 1):
        is_correct = (
            hit["source"] == item["expected_source"]
            and item["expected_section_keyword"].lower() in hit["section"].lower()
        )
        marker = "OK" if is_correct else "FAIL"
        print(f"  [{i}] {marker} {hit['source']} > {hit['section']}  (score: {hit['score']:.4f})")

    correct, top1_returned, rank = evaluate_hit(
        hits, item["expected_source"], item["expected_section_keyword"]
    )
    summary.append({
        "query": query[:45] + "..." if len(query) > 45 else query,
        "correct_at_1": correct,
        "correct_at_rank": rank,
    })

# -----------------------------------------------------------------------------
# Extra paraphrase queries — show BM25's Achilles heel
# -----------------------------------------------------------------------------
print(f"\n\n{'=' * 70}")
print("  BM25 on Pure Paraphrase Queries (no exact keyword match)")
print("=" * 70)

for item in EXTRA_PARAPHRASE_QUERIES:
    query = item["query"]
    print(f"\nQuery: {query}")
    print(f"Note:  {item['note']}")

    hits = bm25_search(query, top_k=3)
    print("Top 3 results:")
    for i, hit in enumerate(hits[:3], 1):
        is_correct = (
            hit["source"] == item["expected_source"]
            and item["expected_section_keyword"].lower() in hit["section"].lower()
        )
        marker = "OK" if is_correct else "FAIL"
        print(f"  [{i}] {marker} {hit['source']} > {hit['section']}  (score: {hit['score']:.4f})")

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
print(f"\n\n{'=' * 70}")
print("  SUMMARY: BM25 Search Performance")
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
print()
print("BM25 Lessons:")
print("  OK BM25 wins when the user uses exact words that appear in the docs.")
print("  OK BM25 wins on 'project limits' and 'Slack' — exact keyword matches.")
print("  FAIL BM25 fails on paraphrase: 'cancel' ≠ 'termination' by keyword count.")
print("  FAIL BM25 fails on 'stop paying' — no keyword overlap at all.")
print()
print("Run 03_hybrid_rrf.py to see how combining both approaches solves this.\n")
