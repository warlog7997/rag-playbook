"""
Chapter 6, Script 3: LLM judge — score generated answers for quality.

For each eval question:
  1. Run full RAG pipeline (hybrid search + answer generation)
  2. Ask Claude Haiku to judge the answer quality:
     {"faithfulness": 1-5, "relevance": 1-5, "completeness": 1-5, "verdict": "pass|fail"}

Faithfulness: Does the answer only use information from the retrieved context?
Relevance:    Does the answer directly address the question?
Completeness: Does the answer cover all aspects of the question?

Uses a subset of the eval dataset (up to 20 questions) for speed/cost.

Run: python 03_llm_judge.py  (from the learn/ directory)
"""
import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import hybrid_search, ask_claude

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
EVAL_PATH = DATA_DIR / "eval_dataset.json"

ANSWER_SYSTEM = """You are a helpful NovaDash support assistant.
Answer the question using ONLY the documentation provided.
Be specific and cite exact details from the docs where possible.
If the answer isn't in the docs, say "I don't have that information." """

JUDGE_SYSTEM = """You are an expert evaluator for an AI question-answering system.
You will receive:
  1. A user question
  2. The expected answer (from ground truth)
  3. The retrieved documentation context
  4. The system-generated answer

Evaluate the generated answer on three dimensions:
  - faithfulness (1-5): Does the answer only use information from the context?
    5 = completely grounded, 1 = makes up information not in context
  - relevance (1-5): Does the answer address the question?
    5 = directly and fully answers, 1 = doesn't address the question
  - completeness (1-5): Does the answer cover all key aspects?
    5 = comprehensive, 1 = misses major aspects

Return ONLY a JSON object:
{
  "faithfulness": <1-5>,
  "relevance": <1-5>,
  "completeness": <1-5>,
  "verdict": "<pass|fail>",
  "notes": "<one sentence explaining the verdict>"
}

Verdict rules:
  pass: all three scores >= 3
  fail: any score < 3"""


def generate_answer(question: str) -> tuple[str, str]:
    """Generate a RAG answer for a question. Returns (answer, context)."""
    hits = hybrid_search(question, top_k=4)
    context = "\n\n---\n\n".join([
        f"Source: {h['source']} | Section: {h['section']}\n{h['text']}"
        for h in hits
    ])
    answer = ask_claude(
        system=ANSWER_SYSTEM,
        user=f"Documentation context:\n{context}\n\nQuestion: {question}",
        model="claude-haiku-4-5-20251001",
    )
    return answer, context


def judge_answer(question: str, expected: str, context: str, answer: str) -> dict:
    """Ask Claude Haiku to judge the quality of an answer."""
    response = ask_claude(
        system=JUDGE_SYSTEM,
        user=f"""Question: {question}

Expected answer: {expected}

Retrieved context (first 800 chars):
{context[:800]}

Generated answer:
{answer}

Evaluate the generated answer.""",
        model="claude-haiku-4-5-20251001",
    )

    try:
        clean = re.sub(r"```json\s*|\s*```", "", response).strip()
        result = json.loads(clean)
        return {
            "faithfulness": int(result.get("faithfulness", 3)),
            "relevance": int(result.get("relevance", 3)),
            "completeness": int(result.get("completeness", 3)),
            "verdict": result.get("verdict", "fail"),
            "notes": result.get("notes", ""),
        }
    except (json.JSONDecodeError, ValueError):
        # Fallback extraction
        f_match = re.search(r'"faithfulness"\s*:\s*(\d)', response)
        r_match = re.search(r'"relevance"\s*:\s*(\d)', response)
        c_match = re.search(r'"completeness"\s*:\s*(\d)', response)
        v_match = re.search(r'"verdict"\s*:\s*"(\w+)"', response)
        return {
            "faithfulness": int(f_match.group(1)) if f_match else 3,
            "relevance": int(r_match.group(1)) if r_match else 3,
            "completeness": int(c_match.group(1)) if c_match else 3,
            "verdict": v_match.group(1) if v_match else "fail",
            "notes": "Score extracted with fallback parsing",
        }


# -----------------------------------------------------------------------------
# Load eval dataset and run evaluation
# -----------------------------------------------------------------------------
print("=" * 65)
print("  Chapter 6 — LLM Judge: Answer Quality Evaluation")
print("=" * 65)

if not EVAL_PATH.exists():
    print(f"ERROR: Eval dataset not found at {EVAL_PATH}")
    print("Run 01_build_eval_dataset.py first.")
    sys.exit(1)

with open(EVAL_PATH, encoding="utf-8") as f:
    all_pairs = json.load(f)

# Use at most 20 questions to keep cost/time manageable
# Prioritize hard questions — they're most interesting
hard_pairs = [p for p in all_pairs if p.get("difficulty") == "hard"]
medium_pairs = [p for p in all_pairs if p.get("difficulty") == "medium"]
easy_pairs = [p for p in all_pairs if p.get("difficulty") == "easy"]

eval_subset = (hard_pairs[:6] + medium_pairs[:8] + easy_pairs[:6])[:20]
print(f"\nEvaluating {len(eval_subset)} questions "
      f"({len([p for p in eval_subset if p.get('difficulty') == 'hard'])} hard, "
      f"{len([p for p in eval_subset if p.get('difficulty') == 'medium'])} medium, "
      f"{len([p for p in eval_subset if p.get('difficulty') == 'easy'])} easy)")

judgments = []

for i, pair in enumerate(eval_subset, 1):
    question = pair["question"]
    expected = pair.get("expected_answer", "")
    print(f"\n[{i}/{len(eval_subset)}] {question[:60]}...")

    # Generate answer
    answer, context = generate_answer(question)

    # Judge answer
    scores = judge_answer(question, expected, context, answer)

    judgments.append({
        "question": question,
        "difficulty": pair.get("difficulty", "unknown"),
        "source_file": pair["source_file"],
        "answer": answer,
        "scores": scores,
    })

    verdict_icon = "OK" if scores["verdict"] == "pass" else "FAIL"
    print(f"  {verdict_icon} F:{scores['faithfulness']} R:{scores['relevance']} "
          f"C:{scores['completeness']} | {scores['notes'][:60]}")

# -----------------------------------------------------------------------------
# Results summary
# -----------------------------------------------------------------------------
print(f"\n\n{'=' * 65}")
print("  LLM Judge Results Summary")
print("=" * 65)

pass_count = sum(1 for j in judgments if j["scores"]["verdict"] == "pass")
fail_count = len(judgments) - pass_count

avg_faith = sum(j["scores"]["faithfulness"] for j in judgments) / len(judgments)
avg_relev = sum(j["scores"]["relevance"] for j in judgments) / len(judgments)
avg_compl = sum(j["scores"]["completeness"] for j in judgments) / len(judgments)

print(f"\nOverall results ({len(judgments)} questions):")
print(f"  Pass: {pass_count} ({pass_count/len(judgments)*100:.0f}%)")
print(f"  Fail: {fail_count} ({fail_count/len(judgments)*100:.0f}%)")
print(f"\nAverage scores:")
print(f"  Faithfulness:  {avg_faith:.2f}/5")
print(f"  Relevance:     {avg_relev:.2f}/5")
print(f"  Completeness:  {avg_compl:.2f}/5")

# Per-difficulty breakdown
print(f"\nBy difficulty:")
for diff in ["easy", "medium", "hard"]:
    diff_results = [j for j in judgments if j.get("difficulty") == diff]
    if diff_results:
        diff_pass = sum(1 for j in diff_results if j["scores"]["verdict"] == "pass")
        print(f"  {diff.capitalize()}: {diff_pass}/{len(diff_results)} pass "
              f"({diff_pass/len(diff_results)*100:.0f}%)")

# Show failures in detail
failures = [j for j in judgments if j["scores"]["verdict"] == "fail"]
if failures:
    print(f"\n\nFailed Answers ({len(failures)}):")
    for fail in failures:
        print(f"\n  Q: {fail['question'][:65]}")
        print(f"  Scores: F:{fail['scores']['faithfulness']} "
              f"R:{fail['scores']['relevance']} C:{fail['scores']['completeness']}")
        print(f"  Notes: {fail['scores']['notes']}")
        print(f"  Answer excerpt: {fail['answer'][:150].strip()}...")

print(f"\n\nRun 04_ragas_eval.py for RAGAS metrics (context precision/recall, etc.).")
