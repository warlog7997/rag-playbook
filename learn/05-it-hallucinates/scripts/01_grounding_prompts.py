"""
Chapter 5, Script 1: Grounding prompts — compare answers WITH and WITHOUT.

Shows how a well-crafted system prompt significantly reduces hallucination
by explicitly constraining the model to the provided context.

Three test questions designed to provoke hallucination:
  1. A question about a feature that doesn't exist ("pause subscription")
  2. A question about a non-existent API endpoint
  3. A question asking for a specific number that requires looking it up

Run: python 01_grounding_prompts.py  (from the learn/ directory)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import hybrid_search, ask_claude

# -----------------------------------------------------------------------------
# System prompts — bad vs good
# -----------------------------------------------------------------------------
WEAK_SYSTEM = """You are a helpful NovaDash support assistant.
Answer questions about NovaDash as helpfully as possible."""

GROUNDED_SYSTEM = """You are a helpful NovaDash support assistant.

CRITICAL RULES:
1. Answer using ONLY the documentation provided in the context below.
2. If the answer is not explicitly stated in the context, respond with:
   "I don't have information about that in the documentation. Please check
   the official NovaDash docs at docs.novadash.io or contact support."
3. Never invent, guess, or extrapolate API endpoints, feature names, or procedures.
4. Never mention features, plans, or behaviors not explicitly described in the context.
5. If you're unsure, say you're unsure — don't guess confidently."""

# -----------------------------------------------------------------------------
# Hallucination-prone test questions
# -----------------------------------------------------------------------------
TEST_CASES = [
    {
        "question": "How do I pause my subscription temporarily?",
        "note": "NovaDash has NO pause feature. Only 'termination'. Weak prompt may invent /pause endpoint.",
        "expected_grounded_response": "Should say this feature doesn't exist in the docs.",
    },
    {
        "question": "What API endpoint do I use to temporarily suspend a user's access without removing them?",
        "note": "The API has deactivate (/users/{id} DELETE) but no 'suspend' endpoint. May hallucinate one.",
        "expected_grounded_response": "Should say this specific endpoint isn't documented.",
    },
    {
        "question": "How long does NovaDash retain data after I delete my account?",
        "note": "Docs say 'terminated' subscription retains data 90 days. 'Delete account' is not exactly the same.",
        "expected_grounded_response": "Should cite the 90-day retention policy or flag uncertainty.",
    },
]


def run_rag_with_prompt(question: str, system_prompt: str, top_k: int = 4) -> tuple[str, list]:
    """Run retrieval + generation with the given system prompt."""
    hits = hybrid_search(question, top_k=top_k)
    context = "\n\n---\n\n".join([
        f"Source: {h['source']} | Section: {h['section']}\n{h['text']}"
        for h in hits
    ])
    answer = ask_claude(
        system=system_prompt,
        user=f"""Documentation context:
{context}

Question: {question}""",
        model="claude-haiku-4-5-20251001",
    )
    return answer, hits


# -----------------------------------------------------------------------------
# Run all test cases
# -----------------------------------------------------------------------------
print("=" * 70)
print("  Chapter 5 — Grounding Prompts: Weak vs Grounded")
print("=" * 70)

for i, case in enumerate(TEST_CASES, 1):
    question = case["question"]
    print(f"\n{'=' * 70}")
    print(f"Test {i}: {question}")
    print(f"Why tricky: {case['note']}")
    print("=" * 70)

    # Run with weak prompt
    print("\n[WEAK PROMPT] (no grounding instructions)")
    print("-" * 50)
    weak_answer, weak_hits = run_rag_with_prompt(question, WEAK_SYSTEM)
    print(f"Retrieved: {[h['source'] + ' > ' + h['section'] for h in weak_hits[:2]]}")
    print(f"\nAnswer:\n{weak_answer}")

    # Run with grounded prompt
    print(f"\n[GROUNDED PROMPT] (with explicit constraints)")
    print("-" * 50)
    grounded_answer, grounded_hits = run_rag_with_prompt(question, GROUNDED_SYSTEM)
    print(f"Retrieved: {[h['source'] + ' > ' + h['section'] for h in grounded_hits[:2]]}")
    print(f"\nAnswer:\n{grounded_answer}")

    # Analysis
    print(f"\nExpected grounded behavior: {case['expected_grounded_response']}")

# -----------------------------------------------------------------------------
# Side-by-side comparison on the most hallucination-prone question
# -----------------------------------------------------------------------------
print(f"\n\n{'=' * 70}")
print("  Hallucination Red Flags to Watch For")
print("=" * 70)
print("""
Red flags in the weak-prompt answers:
  FAIL Mentions an endpoint not in the docs (e.g., /v2/subscription/pause)
  FAIL Invents specific HTTP methods or parameters with confidence
  FAIL States retention periods different from what the docs say
  FAIL Describes a feature flow that doesn't exist in the documentation

Green flags in the grounded-prompt answers:
  OK Says "I don't have information about that" when feature doesn't exist
  OK Cites actual docs content when it answers
  OK Explicitly acknowledges uncertainty
  OK Doesn't fill gaps with plausible-sounding invention

IMPORTANT: Grounding prompts reduce hallucination but don't eliminate it.
The model can still occasionally violate the instruction for very confident-
seeming false information. Use citation enforcement (Script 2) as an
additional layer.
""")
