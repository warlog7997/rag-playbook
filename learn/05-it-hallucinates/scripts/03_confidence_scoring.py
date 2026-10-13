"""
Chapter 5, Script 3: Confidence scoring after answer generation.

After generating an answer, ask a second (cheaper) Claude Haiku call to
evaluate the quality:
  {"confidence": 1-10, "missing_info": "...", "quality": "good|partial|poor"}

Low confidence or "poor" quality triggers a fallback response that tells
the user to verify with official docs or contact support.

This adds a second opinion without adding significant cost (Haiku is cheap).

Run: python 03_confidence_scoring.py  (from the learn/ directory)
"""
import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import hybrid_search, ask_claude

ANSWER_SYSTEM = """You are a helpful NovaDash support assistant.
Answer questions using ONLY the documentation provided. Be specific and concrete.
If the answer isn't fully covered in the context, say what you can and note what's missing."""

SCORING_SYSTEM = """You are a quality evaluator for an AI support system. You will be given:
  1. A user question
  2. The documentation context that was retrieved
  3. The answer that was generated

Evaluate the answer quality and return ONLY a JSON object:
{
  "confidence": <integer 1-10>,
  "missing_info": "<what information is lacking or uncertain, or 'none'>",
  "quality": "<one of: good|partial|poor>",
  "reasoning": "<one sentence explanation>"
}

Scoring guide for "confidence":
  9-10: Answer is fully supported by the context, no gaps
  7-8:  Answer is mostly supported but may have minor gaps
  5-6:  Answer is partially supported — some claims may not be in context
  3-4:  Answer makes claims that go beyond the provided context
  1-2:  Answer contradicts the context or makes up information

Quality:
  good:    Complete, accurate, no concerning gaps
  partial: Some aspects answered, others unclear or missing
  poor:    Major gaps, potential hallucination, or contradicts context"""

# Confidence threshold below which we show a fallback
CONFIDENCE_THRESHOLD = 6


def generate_answer(question: str) -> tuple[str, list]:
    """Generate answer using hybrid retrieval."""
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
    return answer, hits, context


def score_answer(question: str, context: str, answer: str) -> dict:
    """Ask Haiku to score the quality of a generated answer."""
    response = ask_claude(
        system=SCORING_SYSTEM,
        user=f"""Question: {question}

Documentation context (first 1000 chars):
{context[:1000]}

Generated answer:
{answer}

Evaluate this answer.""",
        model="claude-haiku-4-5-20251001",
    )

    try:
        clean = re.sub(r"```json\s*|\s*```", "", response).strip()
        result = json.loads(clean)
        return {
            "confidence": int(result.get("confidence", 5)),
            "missing_info": result.get("missing_info", "unknown"),
            "quality": result.get("quality", "partial"),
            "reasoning": result.get("reasoning", ""),
        }
    except (json.JSONDecodeError, ValueError):
        # Fallback parsing
        conf_match = re.search(r'"confidence"\s*:\s*(\d+)', response)
        qual_match = re.search(r'"quality"\s*:\s*"(\w+)"', response)
        return {
            "confidence": int(conf_match.group(1)) if conf_match else 5,
            "missing_info": "parse error",
            "quality": qual_match.group(1) if qual_match else "partial",
            "reasoning": "Score extracted with fallback parsing",
        }


def format_final_response(answer: str, score: dict) -> str:
    """Return the answer with confidence-appropriate framing."""
    if score["quality"] == "poor" or score["confidence"] < CONFIDENCE_THRESHOLD:
        return (
            f"{answer}\n\n"
            f"⚠️  **Low confidence response** (score: {score['confidence']}/10)\n"
            f"Missing information: {score['missing_info']}\n"
            f"Please verify this answer with the official NovaDash documentation at "
            f"docs.novadash.io or contact support@novadash.io."
        )
    elif score["quality"] == "partial":
        return (
            f"{answer}\n\n"
            f"*Note: This answer may be incomplete. {score['missing_info']}*"
        )
    else:
        return answer


# -----------------------------------------------------------------------------
# Test cases with expected confidence levels
# -----------------------------------------------------------------------------
TEST_QUESTIONS = [
    {
        "question": "What is the session token expiry period in NovaDash?",
        "expected_quality": "good",
        "note": "Directly documented in authentication.md",
    },
    {
        "question": "How do I pause my subscription for 30 days?",
        "expected_quality": "poor",
        "note": "This feature doesn't exist — bot may try to answer anyway",
    },
    {
        "question": "What is NovaDash's uptime SLA for the Pro plan?",
        "expected_quality": "partial",
        "note": "Enterprise SLAs are mentioned but Pro SLA isn't specifically documented",
    },
    {
        "question": "What happens to task assignments after member offboarding?",
        "expected_quality": "good",
        "note": "Well-documented in user-management.md member offboarding section",
    },
]

print("=" * 70)
print("  Chapter 5 — Confidence Scoring After Answer Generation")
print(f"  Threshold: confidence < {CONFIDENCE_THRESHOLD} or quality='poor' > fallback")
print("=" * 70)

for item in TEST_QUESTIONS:
    question = item["question"]
    print(f"\n{'-' * 70}")
    print(f"Question: {question}")
    print(f"Expected quality: {item['expected_quality']} | {item['note']}")
    print("-" * 70)

    # Generate answer
    answer, hits, context = generate_answer(question)
    print(f"\nSources retrieved: {[h['source'] + ' > ' + h['section'][:30] for h in hits[:2]]}")

    # Score it
    score = score_answer(question, context, answer)
    print(f"\nConfidence score: {score['confidence']}/10  |  Quality: {score['quality']}")
    print(f"Missing info: {score['missing_info']}")
    print(f"Reasoning: {score['reasoning']}")

    # Format final response
    final = format_final_response(answer, score)
    print(f"\nFinal response to user:\n{final}")

# -----------------------------------------------------------------------------
# Integration suggestion
# -----------------------------------------------------------------------------
print(f"\n\n{'=' * 70}")
print("  Production Integration Pattern")
print("=" * 70)
print(f"""
In production, plug confidence scoring into your routing logic:

  score = score_answer(question, context, answer)

  if score["quality"] == "poor" or score["confidence"] < {CONFIDENCE_THRESHOLD}:
      # Route to human support queue
      create_support_ticket(question, answer, score)
      response = HUMAN_HANDOFF_MESSAGE
  elif score["quality"] == "partial":
      # Show answer but flag uncertainty
      response = answer + "\\n\\n*Please verify with official docs.*"
  else:
      # Show answer directly
      response = answer

This approach reduces the blast radius of hallucinations:
  - High confidence > users get immediate answers
  - Low confidence > users get honest uncertainty or human help
  - The LLM never silently gives a wrong answer with full confidence

Cost: 1 extra Haiku call per answer (~$0.0003). Worth it.
""")
