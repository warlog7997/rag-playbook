"""
Chapter 2, Script 3: Hybrid search with Reciprocal Rank Fusion (RRF).

Combines vector search + BM25 using RRF:
  RRF_score(doc) = Σ  1 / (rank_in_list + 60)
                  lists

The constant 60 (from the original RRF paper, Cormack et al. 2009) prevents
a document ranked #1 in one list from dominating if it ranks poorly in others.

A document that appears in BOTH retrieval results gets double the RRF contribution,
which is what makes hybrid search so powerful for semantic-gap queries.

Run: python 03_hybrid_rrf.py  (from the learn/ directory)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import vector_search, bm25_search, hybrid_search

# All queries from the previous two scripts
ALL_QUERIES = [
    {
        "query": "How do I cancel my subscription?",
        "expected_source": "billing.md",
        "expected_section_keyword": "termination",
    },
    {
        "query": "How do I remove a team member?",
        "expected_source": "user-management.md",
        "expected_section_keyword": "offboard",
    },
    {
        "query": "What happens when I forget my password?",
        "expected_source": "authentication.md",
        "expected_section_keyword": "recovery",
    },
    {
        "query": "How many projects can I create on the free plan?",
        "expected_source": "projects.md",
        "expected_section_keyword": "limit",
    },
    {
        "query": "How to connect Slack to NovaDash?",
        "expected_source": "integrations.md",
        "expected_section_keyword": "Slack",
    },
    # Paraphrase queries from script 2 extra section
    {
        "query": "stop paying for NovaDash",
        "expected_source": "billing.md",
        "expected_section_keyword": "termination",
    },
    {
        "query": "how to end my account",
        "expected_source": "billing.md",
        "expected_section_keyword": "termination",
    },
]


def get_rank(hits, expected_source, expected_keyword):
    """Return the rank (1-based) of the correct answer, or -1 if not found."""
    for rank, hit in enumerate(hits, 1):
        if (hit["source"] == expected_source
                and expected_keyword.lower() in hit["section"].lower()):
            return rank
    return -1


def rank_to_display(rank):
    """Convert rank integer to display string."""
    if rank == 1:
        return "OK  #1"
    elif rank == 2:
        return "   #2"
    elif rank == 3:
        return "   #3"
    elif rank > 0:
        return f"   #{rank}"
    else:
        return "FAIL miss"


print("=" * 75)
print("  Chapter 2 — Side-by-Side Comparison: Naive vs BM25 vs Hybrid (RRF)")
print("=" * 75)
print()
print("Running all three retrieval methods on every query...")
print("The correct answer is shown as OK #1 (ranked first) or FAIL miss (not found in top 5).\n")

results_table = []

for item in ALL_QUERIES:
    query = item["query"]

    # Run all three retrievers
    naive_hits = vector_search(query, top_k=5)
    bm25_hits = bm25_search(query, top_k=5)
    hybrid_hits = hybrid_search(query, top_k=5, fetch_k=10)

    naive_rank = get_rank(naive_hits, item["expected_source"], item["expected_section_keyword"])
    bm25_rank = get_rank(bm25_hits, item["expected_source"], item["expected_section_keyword"])
    hybrid_rank = get_rank(hybrid_hits, item["expected_source"], item["expected_section_keyword"])

    results_table.append({
        "query": query,
        "naive_rank": naive_rank,
        "bm25_rank": bm25_rank,
        "hybrid_rank": hybrid_rank,
        "naive_correct": naive_rank == 1,
        "bm25_correct": bm25_rank == 1,
        "hybrid_correct": hybrid_rank == 1,
    })

# -----------------------------------------------------------------------------
# Print the comparison table
# -----------------------------------------------------------------------------
col_q = 42
col_r = 12

print(f"{'Query':<{col_q}} {'Naive':^{col_r}} {'BM25':^{col_r}} {'Hybrid':^{col_r}}")
print(f"{'-' * col_q} {'-' * col_r} {'-' * col_r} {'-' * col_r}")

for row in results_table:
    q_display = row["query"][:col_q - 1]
    print(
        f"{q_display:<{col_q}} "
        f"{rank_to_display(row['naive_rank']):^{col_r}} "
        f"{rank_to_display(row['bm25_rank']):^{col_r}} "
        f"{rank_to_display(row['hybrid_rank']):^{col_r}}"
    )

print(f"{'-' * col_q} {'-' * col_r} {'-' * col_r} {'-' * col_r}")

# Recall@1 per approach
n = len(results_table)
naive_r1 = sum(r["naive_correct"] for r in results_table) / n
bm25_r1 = sum(r["bm25_correct"] for r in results_table) / n
hybrid_r1 = sum(r["hybrid_correct"] for r in results_table) / n

print(f"{'Recall@1':<{col_q}} {naive_r1:^{col_r}.2f} {bm25_r1:^{col_r}.2f} {hybrid_r1:^{col_r}.2f}")

# -----------------------------------------------------------------------------
# Deep dive on one query to show HOW RRF combines scores
# -----------------------------------------------------------------------------
deep_query = "How do I cancel my subscription?"
print(f"\n\n{'=' * 75}")
print(f"  RRF Deep Dive: '{deep_query}'")
print("=" * 75)
print()

fetch_k = 8
v_hits = vector_search(deep_query, top_k=fetch_k)
b_hits = bm25_search(deep_query, top_k=fetch_k)
h_hits = hybrid_search(deep_query, top_k=5, fetch_k=fetch_k)

print("Vector search top 3:")
for i, h in enumerate(v_hits[:3], 1):
    print(f"  [{i}] {h['source']} > {h['section']}")

print("\nBM25 search top 3:")
for i, h in enumerate(b_hits[:3], 1):
    print(f"  [{i}] {h['source']} > {h['section']}")

print("\nHybrid (RRF) top 3:")
for i, h in enumerate(h_hits[:3], 1):
    print(f"  [{i}] {h['source']} > {h['section']}  (rrf_score: {h['rrf_score']:.5f})")

print()
print("Explanation:")
print("  The termination/cancellation section appears at rank ~3-5 in vector search")
print("  and rank ~1-2 in BM25 (because 'subscription' is an exact keyword match).")
print("  RRF rewards chunks that appear in BOTH lists — the termination section")
print("  accumulates RRF score from both rankings, pulling it to #1.")
print()
print("Run ../03-irrelevant-results/ to see the next problem: right file, wrong section.\n")
