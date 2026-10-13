"""
Chapter 6, Script 1: Build an evaluation dataset from the NovaDash knowledge base.

Process:
  1. Read all knowledge-base markdown files
  2. For each file, ask Claude Sonnet to generate 10 Q&A pairs
  3. Questions intentionally use DIFFERENT words than the docs (semantic gap testing)
  4. Save to data/eval_dataset.json

The resulting dataset is used by all other Chapter 6 scripts.

Run: python 01_build_eval_dataset.py  (from the learn/ directory)
NOTE: Uses Claude Sonnet for better question quality (~10 API calls, ~$0.05)
"""
import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import ask_claude

KB_DIR = Path(__file__).parent.parent.parent.parent / "knowledge-base"
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
EVAL_PATH = DATA_DIR / "eval_dataset.json"

DATA_DIR.mkdir(exist_ok=True)

QUESTION_GEN_SYSTEM = """You are creating an evaluation dataset for testing a RAG system.
Given a documentation section, generate 10 realistic user questions with expected answers.

CRITICAL RULES:
1. Questions MUST use DIFFERENT words than the documentation (test semantic search)
   - If docs say "subscription termination" > ask about "cancelling my account"
   - If docs say "member offboarding" > ask about "removing someone from the team"
   - If docs say "account recovery via email verification token flow" > ask "forgot password"
   - If docs say "identity provider binding" > ask about "setting up SSO"
2. Questions should be what a REAL USER would type into a support chat
3. Expected answers should be concise (1-3 sentences) based on the doc content
4. Mix difficulty: 3 easy (direct), 4 medium (paraphrase), 3 hard (semantic gap)

Return ONLY a JSON array:
[
  {
    "question": "...",
    "expected_answer": "...",
    "source_file": "filename.md",
    "source_section": "Section Name",
    "difficulty": "easy|medium|hard"
  },
  ...
]"""


def generate_qa_pairs(filename: str, content: str) -> list[dict]:
    """Generate Q&A pairs for a single knowledge base file."""
    # Use only first 3000 chars to stay within context limits and focus on key content
    truncated = content[:3000]

    response = ask_claude(
        system=QUESTION_GEN_SYSTEM,
        user=f"""Documentation file: {filename}

Content:
{truncated}

Generate 10 evaluation questions with expected answers. Remember: use DIFFERENT
words than the documentation to test semantic search.""",
        model="claude-sonnet-4-6",
    )

    try:
        clean = re.sub(r"```json\s*|\s*```", "", response).strip()
        pairs = json.loads(clean)
        if isinstance(pairs, list):
            # Ensure source_file is correct
            for pair in pairs:
                pair["source_file"] = filename
            return pairs
    except (json.JSONDecodeError, ValueError):
        print(f"  Parse error for {filename} — using fallback empty list")
        return []


def build_eval_dataset():
    """Generate Q&A pairs from all knowledge base files and save to JSON."""
    print("=" * 65)
    print("  Building Evaluation Dataset")
    print("=" * 65)
    print()

    all_qa_pairs = []
    md_files = sorted(KB_DIR.glob("*.md"))
    print(f"Found {len(md_files)} knowledge base files.\n")

    for i, md_file in enumerate(md_files, 1):
        print(f"[{i}/{len(md_files)}] Generating questions for {md_file.name}...")
        content = md_file.read_text(encoding="utf-8")

        pairs = generate_qa_pairs(md_file.name, content)
        print(f"  Generated {len(pairs)} Q&A pairs")

        # Show a sample question to verify semantic gap
        if pairs:
            sample = pairs[0]
            print(f"  Sample: '{sample['question']}' [{sample.get('difficulty', 'unknown')}]")

        all_qa_pairs.extend(pairs)

    print(f"\nTotal Q&A pairs generated: {len(all_qa_pairs)}")

    # Save to JSON
    with open(EVAL_PATH, "w", encoding="utf-8") as f:
        json.dump(all_qa_pairs, f, indent=2, ensure_ascii=False)

    print(f"Dataset saved to: {EVAL_PATH}")
    return all_qa_pairs


def print_dataset_stats(pairs: list[dict]):
    """Print statistics about the generated dataset."""
    from collections import Counter

    print(f"\n{'=' * 65}")
    print("  Dataset Statistics")
    print("=" * 65)

    by_source = Counter(p["source_file"] for p in pairs)
    print(f"\nBy source file:")
    for source, count in sorted(by_source.items()):
        print(f"  {source}: {count} questions")

    by_difficulty = Counter(p.get("difficulty", "unknown") for p in pairs)
    print(f"\nBy difficulty:")
    for diff, count in sorted(by_difficulty.items()):
        print(f"  {diff}: {count} questions")

    print(f"\nTotal: {len(pairs)} questions across {len(by_source)} files")

    # Show some examples of intentional semantic gaps
    hard_questions = [p for p in pairs if p.get("difficulty") == "hard"]
    if hard_questions:
        print(f"\nExample hard questions (semantic gap test cases):")
        for q in hard_questions[:5]:
            print(f"  [{q['source_file']}] {q['question']}")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Check if dataset already exists
    if EVAL_PATH.exists():
        existing = json.loads(EVAL_PATH.read_text())
        if len(existing) > 0:
            print(f"Dataset already exists at {EVAL_PATH}")
            print(f"Contains {len(existing)} Q&A pairs.")
            print_dataset_stats(existing)
            print("\nUsing existing dataset. Run 02_recall_mrr.py next.")
            sys.exit(0)
        else:
            print("Found empty dataset, rebuilding...")

    pairs = build_eval_dataset()
    print_dataset_stats(pairs)
    print("\nRun 02_recall_mrr.py to evaluate retrieval quality.")
