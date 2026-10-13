"""
Chapter 6, Script 2: Recall@K and MRR — evaluate retrieval quality.

Loads the eval dataset from data/eval_dataset.json and evaluates:
  - Naive vector search
  - Hybrid RRF search

Metrics:
  Recall@1: correct chunk ranked #1
  Recall@3: correct chunk in top 3
  Recall@5: correct chunk in top 5
  MRR: Mean Reciprocal Rank

Also shows WHICH specific questions each approach gets wrong.

Run: python 02_recall_mrr.py  (from the learn/ directory)
Run 01_build_eval_dataset.py first to generate data/eval_dataset.json
"""
import sys
import json
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import vector_search, hybrid_search

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
EVAL_PATH = DATA_DIR / "eval_dataset.json"


def get_rank(hits: list[dict], expected_source: str, expected_section: str) -> int:
    """
    Find the rank (1-based) of the correct chunk in the retrieved hits.
    Matching: source file must match. Section match is attempted but optional
    since eval dataset section names may differ from actual chunk section names.
    Returns -1 if not found in top K.
    """
    expected_section_lower = expected_section.lower()
    best_rank = -1
    for rank, hit in enumerate(hits, 1):
        if hit["source"] != expected_source:
            continue
        # If section matches (exact or substring), return immediately
        if (expected_section_lower == hit["section"].lower()
                or expected_section_lower in hit["section"].lower()
                or hit["section"].lower() in expected_section_lower):
            return rank
        # Track best source-only match as fallback
        if best_rank == -1:
            best_rank = rank
    # Fall back to source-only match
    return best_rank


def compute_metrics(eval_pairs: list[dict], search_fn, search_name: str, top_k: int = 5):
    """
    Run a search function over all eval pairs and compute retrieval metrics.

    Returns a dict with metrics and per-question details.
    """
    results = []
    reciprocal_ranks = []

    print(f"\n  Running {search_name} on {len(eval_pairs)} questions...")

    for i, pair in enumerate(eval_pairs):
        if (i + 1) % 10 == 0:
            print(f"    [{i+1}/{len(eval_pairs)}]...", end="\r")

        hits = search_fn(pair["question"], top_k=top_k)
        rank = get_rank(hits, pair["source_file"], pair.get("source_section", ""))

        if rank > 0:
            rr = 1.0 / rank
        else:
            rr = 0.0

        reciprocal_ranks.append(rr)
        results.append({
            "question": pair["question"],
            "source_file": pair["source_file"],
            "source_section": pair.get("source_section", ""),
            "difficulty": pair.get("difficulty", "unknown"),
            "rank": rank,
            "correct_at_1": rank == 1,
            "correct_at_3": 0 < rank <= 3,
            "correct_at_5": 0 < rank <= 5,
            "rr": rr,
            "top3_retrieved": [f"{h['source']}>{h['section'][:25]}" for h in hits[:3]],
        })

    print(f"    Done.                              ")

    n = len(results)
    recall_at_1 = sum(r["correct_at_1"] for r in results) / n
    recall_at_3 = sum(r["correct_at_3"] for r in results) / n
    recall_at_5 = sum(r["correct_at_5"] for r in results) / n
    mrr = sum(reciprocal_ranks) / n

    return {
        "name": search_name,
        "recall_at_1": recall_at_1,
        "recall_at_3": recall_at_3,
        "recall_at_5": recall_at_5,
        "mrr": mrr,
        "per_question": results,
    }


# -----------------------------------------------------------------------------
# Load dataset
# -----------------------------------------------------------------------------
print("=" * 65)
print("  Chapter 6 — Retrieval Evaluation: Recall@K and MRR")
print("=" * 65)

if not EVAL_PATH.exists():
    print(f"ERROR: Eval dataset not found at {EVAL_PATH}")
    print("Run 01_build_eval_dataset.py first.")
    sys.exit(1)

with open(EVAL_PATH, encoding="utf-8") as f:
    eval_pairs = json.load(f)

print(f"\nLoaded {len(eval_pairs)} evaluation questions.")

# -----------------------------------------------------------------------------
# Run evaluations
# -----------------------------------------------------------------------------
print("\nEvaluating retrieval methods...")

naive_results = compute_metrics(
    eval_pairs,
    search_fn=lambda q, top_k: vector_search(q, top_k=top_k),
    search_name="Naive Vector",
    top_k=5,
)

hybrid_results = compute_metrics(
    eval_pairs,
    search_fn=lambda q, top_k: hybrid_search(q, top_k=top_k, fetch_k=top_k * 2),
    search_name="Hybrid RRF",
    top_k=5,
)

# -----------------------------------------------------------------------------
# Print comparison table
# -----------------------------------------------------------------------------
print(f"\n\n{'=' * 65}")
print("  Retrieval Metrics Comparison")
print("=" * 65)
print(f"\n{'Phase':<22} {'Recall@1':>9} {'Recall@3':>9} {'Recall@5':>9} {'MRR':>9}")
print(f"{'-' * 22} {'-' * 9} {'-' * 9} {'-' * 9} {'-' * 9}")

for res in [naive_results, hybrid_results]:
    print(
        f"{res['name']:<22} "
        f"{res['recall_at_1']:>9.3f} "
        f"{res['recall_at_3']:>9.3f} "
        f"{res['recall_at_5']:>9.3f} "
        f"{res['mrr']:>9.3f}"
    )

# Delta row
d1 = hybrid_results["recall_at_1"] - naive_results["recall_at_1"]
d3 = hybrid_results["recall_at_3"] - naive_results["recall_at_3"]
d5 = hybrid_results["recall_at_5"] - naive_results["recall_at_5"]
dm = hybrid_results["mrr"] - naive_results["mrr"]
print(f"{'-' * 22} {'-' * 9} {'-' * 9} {'-' * 9} {'-' * 9}")
print(f"{'Hybrid improvement':<22} {d1:>+9.3f} {d3:>+9.3f} {d5:>+9.3f} {dm:>+9.3f}")

# -----------------------------------------------------------------------------
# Show which questions each approach gets wrong
# -----------------------------------------------------------------------------
print(f"\n\n{'=' * 65}")
print("  Questions Naive Gets Wrong (Correct Source Not at Rank 1)")
print("=" * 65)

naive_failures = [r for r in naive_results["per_question"] if not r["correct_at_1"]]
print(f"\nNaive failures: {len(naive_failures)}/{len(eval_pairs)}")
for fail in naive_failures[:10]:
    print(f"\n  Q: {fail['question'][:65]}")
    print(f"     Expected: {fail['source_file']} > {fail['source_section'][:35]}")
    print(f"     Got rank: {fail['rank']} | Top retrieved: {fail['top3_retrieved'][0] if fail['top3_retrieved'] else 'none'}")
    print(f"     Difficulty: {fail['difficulty']}")

print(f"\n\n{'=' * 65}")
print("  Questions Hybrid Gets Wrong")
print("=" * 65)

hybrid_failures = [r for r in hybrid_results["per_question"] if not r["correct_at_1"]]
print(f"\nHybrid failures: {len(hybrid_failures)}/{len(eval_pairs)}")
for fail in hybrid_failures[:10]:
    print(f"\n  Q: {fail['question'][:65]}")
    print(f"     Expected: {fail['source_file']} > {fail['source_section'][:35]}")
    print(f"     Got rank: {fail['rank']} | Top retrieved: {fail['top3_retrieved'][0] if fail['top3_retrieved'] else 'none'}")
    print(f"     Difficulty: {fail['difficulty']}")

# -----------------------------------------------------------------------------
# Breakdown by difficulty
# -----------------------------------------------------------------------------
print(f"\n\n{'=' * 65}")
print("  Recall@1 Breakdown by Question Difficulty")
print("=" * 65)

for diff in ["easy", "medium", "hard"]:
    naive_diff = [r for r in naive_results["per_question"] if r.get("difficulty") == diff]
    hybrid_diff = [r for r in hybrid_results["per_question"] if r.get("difficulty") == diff]

    if naive_diff:
        naive_r1 = sum(r["correct_at_1"] for r in naive_diff) / len(naive_diff)
        hybrid_r1 = sum(r["correct_at_1"] for r in hybrid_diff) / len(hybrid_diff)
        print(f"\n  {diff.capitalize()} ({len(naive_diff)} questions):")
        print(f"    Naive:  {naive_r1:.3f}")
        print(f"    Hybrid: {hybrid_r1:.3f}  (delta: {hybrid_r1 - naive_r1:+.3f})")

print(f"\n\n{'=' * 65}")
print("  Next Steps")
print("=" * 65)
print("""
Run 03_llm_judge.py to evaluate ANSWER quality (not just retrieval).
Run 04_ragas_eval.py for RAGAS metrics (context precision/recall, faithfulness).

The recall numbers here measure retrieval only — a system can have good
retrieval and still generate poor answers (if the prompting is bad).
Use LLM judge to evaluate end-to-end quality.
""")
