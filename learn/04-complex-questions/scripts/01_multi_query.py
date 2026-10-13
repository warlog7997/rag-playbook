"""
Chapter 4, Script 1: Multi-query (query expansion) for complex questions.

Single queries miss multi-faceted answers. This script generates 4 query
variants using Claude, runs hybrid search on each, deduplicates by chunk ID,
then combines into a richer context pool.

Run: python 01_multi_query.py  (from the learn/ directory)
"""
import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import hybrid_search, ask_claude, format_results

# The complex query that stumps single-query RAG
COMPLEX_QUERY = (
    "Compare how Free and Pro plans handle user limits and project limits, "
    "and what happens when you exceed those limits."
)

QUERY_GEN_SYSTEM = """You are a search query generator. Given a complex user question,
generate 4 focused search queries that together will retrieve all the information needed
to answer the question.

Return ONLY a JSON array of 4 query strings, no explanation:
["query 1", "query 2", "query 3", "query 4"]"""


def generate_query_variants(question: str) -> list[str]:
    """Ask Claude Haiku to generate 4 search query variants for a complex question."""
    response = ask_claude(
        system=QUERY_GEN_SYSTEM,
        user=f"Complex question: {question}",
        model="claude-haiku-4-5-20251001",
    )

    try:
        clean = re.sub(r"```json\s*|\s*```", "", response).strip()
        queries = json.loads(clean)
        if isinstance(queries, list):
            return [str(q) for q in queries[:4]]
    except (json.JSONDecodeError, ValueError):
        # Fallback: extract quoted strings
        queries = re.findall(r'"([^"]{10,})"', response)
        if queries:
            return queries[:4]

    # Hard fallback if parsing fails entirely
    return [
        "Free plan user limits and restrictions",
        "Pro plan features user and project limits",
        "what happens when exceeding plan limits",
        "plan comparison Free Pro features",
    ]


# -----------------------------------------------------------------------------
# STEP 1: Show what single-query RAG retrieves
# -----------------------------------------------------------------------------
print("=" * 70)
print("  Multi-Query RAG: Handling Complex Questions")
print("=" * 70)
print(f"\nComplex Query:\n  '{COMPLEX_QUERY}'\n")

print("Step 1: Single-query retrieval (what naive RAG does)...")
single_hits = hybrid_search(COMPLEX_QUERY, top_k=5)

print(f"\nSingle query retrieved {len(single_hits)} chunks:")
sources_seen = set()
for i, hit in enumerate(single_hits, 1):
    sources_seen.add(hit["source"])
    print(f"  [{i}] {hit['source']} > {hit['section']}")

print(f"\nSources covered: {sources_seen}")
print(f"Problem: {len(sources_seen)} sources found, but we need billing.md, "
      f"projects.md, AND user-management.md to answer fully.")

# -----------------------------------------------------------------------------
# STEP 2: Generate query variants
# -----------------------------------------------------------------------------
print("\n\nStep 2: Generating query variants with Claude Haiku...")
queries = generate_query_variants(COMPLEX_QUERY)
print(f"\nGenerated {len(queries)} queries:")
for i, q in enumerate(queries, 1):
    print(f"  [{i}] {q}")

# -----------------------------------------------------------------------------
# STEP 3: Run hybrid search for each variant and deduplicate
# -----------------------------------------------------------------------------
print("\n\nStep 3: Running hybrid search for each variant...")

all_hits = {}  # id > hit (deduplication)
query_hit_counts = []

for i, q in enumerate(queries, 1):
    hits = hybrid_search(q, top_k=5, fetch_k=10)
    new_count = 0
    for hit in hits:
        if hit["id"] not in all_hits:
            all_hits[hit["id"]] = hit
            new_count += 1
    query_hit_counts.append((q, len(hits), new_count))
    print(f"  Query {i}: retrieved {len(hits)} > {new_count} new unique chunks "
          f"(running total: {len(all_hits)})")

pooled_hits = list(all_hits.values())
print(f"\nFinal pool: {len(pooled_hits)} unique chunks "
      f"(vs {len(single_hits)} from single query)")

# -----------------------------------------------------------------------------
# STEP 4: Show what sources are now covered
# -----------------------------------------------------------------------------
print("\nStep 4: Source coverage in the combined pool:")
from collections import Counter
source_counts = Counter(h["source"] for h in pooled_hits)
for source, count in sorted(source_counts.items()):
    print(f"  {source}: {count} chunk(s)")

target_sources = {"billing.md", "projects.md", "user-management.md"}
covered = set(source_counts.keys()) & target_sources
print(f"\nTarget sources covered: {covered}")
print(f"Coverage: {len(covered)}/{len(target_sources)} needed sources")

# -----------------------------------------------------------------------------
# STEP 5: Generate final answer using the combined context
# -----------------------------------------------------------------------------
print("\n\nStep 5: Generating answer from combined context...")

# Sort pooled hits by RRF score if available, otherwise by regular score
pooled_hits.sort(key=lambda h: h.get("rrf_score", h.get("score", 0)), reverse=True)

# Take top 8 most relevant chunks for the context
top_hits = pooled_hits[:8]
context = "\n\n---\n\n".join([
    f"Source: {h['source']} | Section: {h['section']}\n{h['text']}"
    for h in top_hits
])

answer = ask_claude(
    system="""You are a helpful NovaDash support assistant. Answer the user's question
using ONLY the provided documentation context. Structure your answer clearly with
headers for each aspect of the question. Be specific and cite the exact limits mentioned
in the docs.""",
    user=f"""Documentation context:
{context}

Question: {COMPLEX_QUERY}""",
)

print("\n" + "=" * 70)
print("  Final Answer (from combined context)")
print("=" * 70)
print(answer)
print()

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
print("=" * 70)
print("  Summary")
print("=" * 70)
print(f"""
Single query: {len(single_hits)} chunks, {len(sources_seen)} sources
Multi-query:  {len(pooled_hits)} chunks, {len(source_counts)} sources

The multi-query approach expanded coverage from {len(sources_seen)} to
{len(source_counts)} sources, enabling a complete answer.

Cost: {len(queries) + 2} API calls (1 for query generation, {len(queries)} for search,
      1 for answer generation) vs 2 calls for single-query RAG.

Next: Run 02_query_decomposition.py for a more structured approach
      that answers each sub-question independently.
""")
