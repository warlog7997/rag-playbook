"""
Chapter 4, Script 2: Query decomposition for structured complex answers.

Instead of generating query variants (multi-query), we break the question
into 2-3 focused sub-questions and answer each one independently.
Then we combine the sub-answers into a final comprehensive response.

This is better than multi-query for "compare X and Y" style questions because:
  - Each sub-question has a dedicated answer (no mixing)
  - The final synthesis has structured sub-answers to work from
  - Easier to debug which part failed if the answer is wrong

Run: python 02_query_decomposition.py  (from the learn/ directory)
"""
import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import hybrid_search, ask_claude

COMPLEX_QUERY = (
    "Compare how Free and Pro plans handle user limits and project limits, "
    "and what happens when you exceed those limits."
)

DECOMPOSE_SYSTEM = """You are a question analysis assistant. Your job is to break down
a complex question into 2-4 focused, self-contained sub-questions that together
cover all aspects of the original question.

Return ONLY a JSON array of sub-questions:
[
  {"sub_question": "...", "aspect": "..."},
  ...
]

Each sub-question should be answerable independently from documentation."""

SUB_ANSWER_SYSTEM = """You are a helpful NovaDash support assistant. Answer the user's
question using ONLY the provided documentation context. Be specific and concrete —
cite exact limits, numbers, and policies from the docs. If the docs don't have the
answer, say so clearly."""

SYNTHESIZE_SYSTEM = """You are a helpful NovaDash support assistant. You have received
answers to several sub-questions that together address a user's complex question.
Synthesize these answers into a single, well-structured response.

Use markdown headers to organize the answer. Be concise — don't repeat information."""


def decompose_question(question: str) -> list[dict]:
    """Break a complex question into focused sub-questions."""
    response = ask_claude(
        system=DECOMPOSE_SYSTEM,
        user=f"Complex question: {question}",
        model="claude-haiku-4-5-20251001",
    )

    try:
        clean = re.sub(r"```json\s*|\s*```", "", response).strip()
        items = json.loads(clean)
        if isinstance(items, list):
            return items
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback decomposition
    return [
        {"sub_question": "What are the user and project limits on the Free plan?",
         "aspect": "Free plan limits"},
        {"sub_question": "What are the user and project limits on the Pro plan?",
         "aspect": "Pro plan limits"},
        {"sub_question": "What happens when you exceed plan limits in NovaDash?",
         "aspect": "Exceeding limits"},
    ]


def answer_sub_question(sub_question: str, top_k: int = 4) -> dict:
    """Retrieve context and generate an answer for a single sub-question."""
    hits = hybrid_search(sub_question, top_k=top_k)
    context = "\n\n---\n\n".join([
        f"Source: {h['source']} | Section: {h['section']}\n{h['text']}"
        for h in hits
    ])
    answer = ask_claude(
        system=SUB_ANSWER_SYSTEM,
        user=f"Documentation context:\n{context}\n\nQuestion: {sub_question}",
        model="claude-haiku-4-5-20251001",
    )
    return {
        "sub_question": sub_question,
        "answer": answer,
        "sources": [f"{h['source']} > {h['section']}" for h in hits[:3]],
    }


# -----------------------------------------------------------------------------
# Main pipeline
# -----------------------------------------------------------------------------
print("=" * 70)
print("  Query Decomposition RAG")
print("=" * 70)
print(f"\nOriginal Question:\n  '{COMPLEX_QUERY}'\n")

# Step 1: Decompose
print("Step 1: Decomposing into sub-questions...")
sub_questions = decompose_question(COMPLEX_QUERY)
print(f"\nDecomposed into {len(sub_questions)} sub-questions:")
for i, sq in enumerate(sub_questions, 1):
    aspect = sq.get("aspect", "")
    q = sq.get("sub_question", str(sq))
    print(f"  [{i}] ({aspect}): {q}")

# Step 2: Answer each sub-question
print("\n\nStep 2: Answering each sub-question independently...")
sub_answers = []

for i, sq in enumerate(sub_questions, 1):
    q = sq.get("sub_question", str(sq))
    aspect = sq.get("aspect", f"Part {i}")

    print(f"\n  Sub-question {i}: {q}")
    result = answer_sub_question(q)

    print(f"  Sources used: {', '.join(result['sources'][:2])}")
    print(f"  Answer snippet: {result['answer'][:200].strip()}...")
    sub_answers.append(result)

# Step 3: Synthesize
print("\n\nStep 3: Synthesizing sub-answers into final response...")

synthesis_context = "\n\n---\n\n".join([
    f"Sub-question {i + 1}: {sa['sub_question']}\n\nAnswer: {sa['answer']}"
    for i, sa in enumerate(sub_answers)
])

final_answer = ask_claude(
    system=SYNTHESIZE_SYSTEM,
    user=f"""Original question: {COMPLEX_QUERY}

Sub-question answers:
{synthesis_context}

Synthesize these into a comprehensive, well-organized answer.""",
    model="claude-haiku-4-5-20251001",
)

print("\n" + "=" * 70)
print("  Final Synthesized Answer")
print("=" * 70)
print(final_answer)

# -----------------------------------------------------------------------------
# Comparison: direct vs decomposed
# -----------------------------------------------------------------------------
print("\n\n" + "=" * 70)
print("  Direct Answer (without decomposition) for Comparison")
print("=" * 70)
print("Running single-query RAG on the original question...")

direct_hits = hybrid_search(COMPLEX_QUERY, top_k=4)
direct_context = "\n\n---\n\n".join([
    f"Source: {h['source']} | Section: {h['section']}\n{h['text']}"
    for h in direct_hits
])
direct_answer = ask_claude(
    system=SUB_ANSWER_SYSTEM,
    user=f"Documentation context:\n{direct_context}\n\nQuestion: {COMPLEX_QUERY}",
    model="claude-haiku-4-5-20251001",
)

print("\nDirect answer:")
print(direct_answer)

print("\n\n" + "=" * 70)
print("  Comparison")
print("=" * 70)
print(f"""
Direct answer sources: {[h['source'] for h in direct_hits[:3]]}
Decomposed answer sources: {list(set(s for sa in sub_answers for s in sa['sources']))}

Decomposition advantages:
  OK Each part of the question is specifically addressed
  OK More sources retrieved (3 files vs typically 1-2 with direct)
  OK Structured final answer with clear sections
  OK Easier to identify which sub-question has poor coverage

Cost: {len(sub_questions) + 2} API calls vs 2 for direct RAG

Next: Run 03_agentic_react.py for the most powerful approach —
      an agent that decides what to search for based on what it finds.
""")
