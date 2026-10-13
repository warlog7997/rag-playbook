"""
Chapter 5, Script 2: Citation enforcement — force the model to cite sources,
then verify those citations exist in the knowledge base.

Pipeline:
  1. Retrieve chunks
  2. Ask Claude to answer WITH mandatory citations in [source.md::section] format
  3. Parse citations from response using regex
  4. Verify each citation exists in the ChromaDB collection
  5. Flag responses with invented citations

This catches a specific type of hallucination: the model cites a source that
doesn't exist — often the strongest signal that it's making things up.

Run: python 02_citation.py  (from the learn/ directory)
"""
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import hybrid_search, ask_claude, load_chroma

CITATION_SYSTEM = """You are a helpful NovaDash support assistant.

Answer questions using ONLY the documentation provided. After every factual claim,
you MUST cite the source using this exact format: [source_file::section_name]

Example of proper citation:
  "The Free plan supports up to 5 users [user-management.md::bulk_user_import_via_csv]
  and 3 active projects [projects.md::project_limits_by_plan]."

Rules:
1. Every factual claim MUST be followed by a citation in [file::section] format.
2. Use the EXACT source filename and section name from the context provided.
3. Do not cite sources not present in the context below.
4. If you cannot cite a claim, do not make it."""


def extract_citations(text: str) -> list[str]:
    """
    Extract all [file.md::section] citations from response text.
    Returns a list of citation strings like 'billing.md::subscription_lifecycle'.
    """
    pattern = r'\[([a-z-]+\.md)::([\w_]+)\]'
    matches = re.findall(pattern, text)
    return [f"{source}::{section}" for source, section in matches]


def verify_citation(citation: str) -> dict:
    """
    Check if a citation exists in the ChromaDB collection.
    Returns {"exists": bool, "citation": str, "closest_id": str|None}
    """
    collection = load_chroma()

    # The chunk ID format is: stem::section_title_as_lower_slug
    # e.g., "billing::subscription_termination_with_data_retention_policy"
    parts = citation.split("::")
    if len(parts) != 2:
        return {"exists": False, "citation": citation, "closest_id": None}

    source_file, section_slug = parts

    # Try exact match first
    try:
        result = collection.get(ids=[citation])
        if result["ids"]:
            return {"exists": True, "citation": citation, "closest_id": citation}
    except Exception:
        pass

    # Try matching source file + section keyword
    # Get all chunks and check if any match the source
    all_chunks = collection.get(
        where={"source": source_file},
        include=["metadatas"],
    )

    if not all_chunks["ids"]:
        return {"exists": False, "citation": citation, "closest_id": None,
                "reason": f"Source file '{source_file}' not found in index"}

    # Check if the section slug appears in any chunk ID from this file
    for chunk_id in all_chunks["ids"]:
        if section_slug in chunk_id.lower():
            return {"exists": True, "citation": citation, "closest_id": chunk_id}

    # Source file exists but section not found
    available_sections = [cid.split("::")[-1] for cid in all_chunks["ids"][:5]]
    return {
        "exists": False,
        "citation": citation,
        "closest_id": None,
        "reason": f"Section '{section_slug}' not found in {source_file}. "
                  f"Available: {available_sections}",
    }


def run_with_citations(question: str, top_k: int = 4) -> dict:
    """Run RAG with citation enforcement, then verify all citations."""
    hits = hybrid_search(question, top_k=top_k)
    context = "\n\n---\n\n".join([
        f"Source: {h['source']} | Section: {h['section']}\n{h['text']}"
        for h in hits
    ])

    answer = ask_claude(
        system=CITATION_SYSTEM,
        user=f"""Documentation context:
{context}

Question: {question}""",
        model="claude-haiku-4-5-20251001",
    )

    citations = extract_citations(answer)
    verifications = [verify_citation(c) for c in citations]

    all_valid = all(v["exists"] for v in verifications)
    invented = [v for v in verifications if not v["exists"]]

    return {
        "question": question,
        "answer": answer,
        "citations": citations,
        "verifications": verifications,
        "all_valid": all_valid,
        "invented_citations": invented,
    }


# -----------------------------------------------------------------------------
# Test cases — mix of good and hallucination-prone questions
# -----------------------------------------------------------------------------
TEST_QUESTIONS = [
    "What is the session token expiry for NovaDash?",
    "How do I cancel my NovaDash subscription?",
    "How do I pause my subscription temporarily?",  # Feature doesn't exist
    "What is the rate limit for the Free plan API?",
    "How do I set up GitHub auto-status updates for tasks?",
]

print("=" * 70)
print("  Chapter 5 — Citation Enforcement and Verification")
print("=" * 70)
print("""
Format: [source.md::section_name]
  OK = Citation verified in knowledge base
  FAIL = Citation NOT found — potential hallucination!
""")

for question in TEST_QUESTIONS:
    print(f"\n{'-' * 70}")
    print(f"Question: {question}")
    print("-" * 70)

    result = run_with_citations(question)
    print(f"\nAnswer:\n{result['answer']}")

    print(f"\nCitation verification ({len(result['citations'])} citation(s) found):")
    if not result["citations"]:
        print("  ⚠  No citations found in response — model did not follow citation instruction")
    else:
        for v in result["verifications"]:
            status = "OK" if v["exists"] else "FAIL"
            print(f"  [{status}] {v['citation']}")
            if not v["exists"] and "reason" in v:
                print(f"        Reason: {v['reason']}")

    if result["invented_citations"]:
        print(f"\n  ⚠  HALLUCINATION ALERT: {len(result['invented_citations'])} invented citation(s)!")
        for inv in result["invented_citations"]:
            print(f"     '{inv['citation']}' does not exist in the knowledge base")
    elif result["all_valid"] and result["citations"]:
        print(f"\n  OK All citations verified — response is grounded")

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
print(f"\n\n{'=' * 70}")
print("  Citation Enforcement: Key Points")
print("=" * 70)
print("""
What citation enforcement catches:
  OK Invented sources (file that doesn't exist)
  OK Invented sections (section not in the knowledge base)
  OK Uncited claims (model didn't follow the instruction = suspicious)

What it doesn't catch:
  FAIL Misattributed citations (correct section, wrong claim about its content)
  FAIL Subtle factual errors within the cited section
  FAIL Omissions (correct but incomplete answers)

In production: flag any response with an uncited claim or an invented citation
for human review. Log the query, retrieved context, and response for audit.

Next: Run 03_confidence_scoring.py to add a quality gate on top of citations.
""")
