"""
Chapter 6, Script 4: RAGAS evaluation — automated RAG metrics.

RAGAS (Retrieval Augmented Generation Assessment) is an open-source framework
that computes metrics for evaluating RAG systems:

  context_precision:  Of the retrieved chunks, what fraction were actually useful
                      for generating the answer? (Precision of retrieval)

  context_recall:     Of all information needed to answer the question, what
                      fraction did the retrieved context contain? (Recall of retrieval)

  faithfulness:       Does the generated answer contradict the retrieved context?
                      (Hallucination detection via NLI)

  answer_relevancy:   Is the generated answer relevant to the question asked?
                      (Does it address what was asked, not something adjacent)

All four metrics together give a comprehensive view of RAG quality.

Run: python 04_ragas_eval.py  (from the learn/ directory)
Requirements: pip install ragas langchain-anthropic
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
EVAL_PATH = DATA_DIR / "eval_dataset.json"

# -----------------------------------------------------------------------------
# Check RAGAS is available
# -----------------------------------------------------------------------------
try:
    from ragas import evaluate
    from ragas.metrics import (
        context_precision,
        context_recall,
        faithfulness,
        answer_relevancy,
    )
    from datasets import Dataset
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False

try:
    from langchain_anthropic import ChatAnthropic
    LANGCHAIN_AVAILABLE = True
except (ImportError, AttributeError):
    LANGCHAIN_AVAILABLE = False


def build_ragas_dataset(eval_pairs: list[dict], n: int = 15) -> list[dict]:
    """
    Build the RAGAS dataset format from our eval pairs.

    RAGAS expects:
      question:    The user question
      answer:      The generated answer
      contexts:    List of retrieved chunk texts
      ground_truth: The expected correct answer
    """
    from utils import hybrid_search, ask_claude

    ANSWER_SYSTEM = """You are a helpful NovaDash support assistant.
Answer the question using ONLY the documentation provided. Be specific and direct."""

    # Use a subset for speed
    subset = eval_pairs[:n]
    ragas_rows = []

    print(f"Building RAGAS dataset from {len(subset)} questions...")

    for i, pair in enumerate(subset, 1):
        question = pair["question"]
        print(f"  [{i}/{len(subset)}] {question[:55]}...", end="", flush=True)

        # Retrieve
        hits = hybrid_search(question, top_k=4)
        contexts = [h["text"] for h in hits]

        # Generate answer
        context_str = "\n\n---\n\n".join([
            f"Source: {h['source']} | Section: {h['section']}\n{h['text']}"
            for h in hits
        ])
        answer = ask_claude(
            system=ANSWER_SYSTEM,
            user=f"Documentation context:\n{context_str}\n\nQuestion: {question}",
            model="claude-haiku-4-5-20251001",
        )

        ragas_rows.append({
            "question": question,
            "answer": answer,
            "contexts": contexts,
            "ground_truth": pair.get("expected_answer", ""),
        })
        print(" done")

    return ragas_rows


def run_ragas_evaluation(ragas_rows: list[dict]) -> dict:
    """Run RAGAS metrics on the dataset."""
    import keyring
    api_key = keyring.get_password("Anthorpic", "API_KEY")

    # Configure RAGAS to use Claude
    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=api_key,
    )

    dataset = Dataset.from_list(ragas_rows)

    print("\nRunning RAGAS evaluation...")
    print("(This makes many API calls — may take 2-5 minutes)\n")

    result = evaluate(
        dataset=dataset,
        metrics=[
            context_precision,
            context_recall,
            faithfulness,
            answer_relevancy,
        ],
        llm=llm,
        raise_exceptions=False,
    )

    return result


def print_ragas_report(result, ragas_rows: list[dict]):
    """Print a formatted RAGAS evaluation report."""
    print("\n" + "=" * 65)
    print("  RAGAS Evaluation Report")
    print("=" * 65)

    # Overall scores
    df = result.to_pandas()
    print("\nOverall Scores:")
    print(f"  Context Precision:   {df['context_precision'].mean():.3f}")
    print(f"  Context Recall:      {df['context_recall'].mean():.3f}")
    print(f"  Faithfulness:        {df['faithfulness'].mean():.3f}")
    print(f"  Answer Relevancy:    {df['answer_relevancy'].mean():.3f}")

    # Metric explanations
    print(f"\nMetric Explanations:")
    print(f"  Context Precision {df['context_precision'].mean():.3f}")
    print(f"    > {'OK Good' if df['context_precision'].mean() > 0.7 else 'FAIL Needs improvement'}")
    print(f"    > Of retrieved chunks, this fraction were relevant to the answer.")
    if df["context_precision"].mean() < 0.6:
        print(f"    > Low precision: retrieving too many irrelevant chunks (noise).")
        print(f"       Fix: reduce top_k or add reranking to filter out irrelevant chunks.")

    print(f"\n  Context Recall {df['context_recall'].mean():.3f}")
    print(f"    > {'OK Good' if df['context_recall'].mean() > 0.7 else 'FAIL Needs improvement'}")
    print(f"    > Of all information needed, this fraction was retrieved.")
    if df["context_recall"].mean() < 0.6:
        print(f"    > Low recall: missing relevant chunks (retrieval gap).")
        print(f"       Fix: increase top_k or use hybrid/multi-query retrieval.")

    print(f"\n  Faithfulness {df['faithfulness'].mean():.3f}")
    print(f"    > {'OK Good' if df['faithfulness'].mean() > 0.8 else 'FAIL Needs improvement'}")
    print(f"    > This fraction of claims in the answer are supported by context.")
    if df["faithfulness"].mean() < 0.7:
        print(f"    > Low faithfulness: possible hallucination detected.")
        print(f"       Fix: stronger grounding prompts, citation enforcement (Chapter 5).")

    print(f"\n  Answer Relevancy {df['answer_relevancy'].mean():.3f}")
    print(f"    > {'OK Good' if df['answer_relevancy'].mean() > 0.8 else 'FAIL Needs improvement'}")
    print(f"    > How well the answer addresses the actual question.")
    if df["answer_relevancy"].mean() < 0.7:
        print(f"    > Low relevancy: answers are off-topic or tangential.")
        print(f"       Fix: improve retrieval so context is more focused; add query rewriting.")

    # Per-question breakdown for worst performers
    print(f"\nWorst performing questions (by combined score):")
    df["combined"] = (
        df["context_precision"] + df["context_recall"]
        + df["faithfulness"] + df["answer_relevancy"]
    ) / 4

    worst = df.nsmallest(5, "combined")
    for _, row in worst.iterrows():
        idx = row.name
        if idx < len(ragas_rows):
            q = ragas_rows[idx]["question"][:60]
            print(f"\n  Q: {q}...")
            print(f"     Precision:{row['context_precision']:.2f} "
                  f"Recall:{row['context_recall']:.2f} "
                  f"Faith:{row['faithfulness']:.2f} "
                  f"Relev:{row['answer_relevancy']:.2f}")


def print_manual_report(ragas_rows: list[dict]):
    """Fallback report when RAGAS is not installed."""
    print("\n" + "=" * 65)
    print("  RAGAS Not Available — Manual Summary")
    print("=" * 65)
    print(f"\nBuilt RAGAS dataset with {len(ragas_rows)} rows.")
    print("\nTo run RAGAS evaluation, install the package:")
    print("  pip install ragas langchain-anthropic")
    print()
    print("RAGAS metrics that would be computed:")
    print("  context_precision  — fraction of retrieved chunks actually useful")
    print("  context_recall     — fraction of needed information that was retrieved")
    print("  faithfulness       — fraction of claims supported by context")
    print("  answer_relevancy   — how well the answer addresses the question")
    print()
    print("Expected results based on Chapter 6 hybrid search (approximate):")
    print("  Context Precision:  0.65-0.75")
    print("  Context Recall:     0.70-0.80")
    print("  Faithfulness:       0.85-0.95")
    print("  Answer Relevancy:   0.80-0.90")
    print()

    print("First 3 questions in the dataset:")
    for row in ragas_rows[:3]:
        print(f"\n  Q: {row['question'][:65]}")
        print(f"  A: {row['answer'][:120].strip()}...")
        print(f"  Contexts: {len(row['contexts'])} chunks retrieved")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
print("=" * 65)
print("  Chapter 6 — RAGAS Evaluation")
print("=" * 65)

if not EVAL_PATH.exists():
    print(f"ERROR: Eval dataset not found at {EVAL_PATH}")
    print("Run 01_build_eval_dataset.py first.")
    sys.exit(1)

with open(EVAL_PATH, encoding="utf-8") as f:
    all_pairs = json.load(f)

print(f"\nLoaded {len(all_pairs)} eval questions.")

# Build RAGAS dataset
ragas_rows = build_ragas_dataset(all_pairs, n=15)

if not RAGAS_AVAILABLE or not LANGCHAIN_AVAILABLE:
    print("\nNote: ragas or langchain-anthropic not installed.")
    print("Showing manual dataset summary instead.\n")
    print_manual_report(ragas_rows)
else:
    result = run_ragas_evaluation(ragas_rows)
    print_ragas_report(result, ragas_rows)

print(f"\n\n{'=' * 65}")
print("  Congratulations — You've Completed the Learning Track!")
print("=" * 65)
print("""
You now know how to:
  OK Build a basic RAG system (Chapter 1)
  OK Fix semantic gaps with hybrid search (Chapter 2)
  OK Improve precision with reranking (Chapter 3)
  OK Handle complex multi-part questions (Chapter 4)
  OK Detect and prevent hallucination (Chapter 5)
  OK Measure if it's working (Chapter 6)

These 6 chapters cover the exact problems we encountered building real
production AI systems for healthcare and SaaS platforms.

Next: See the production/ directory for advanced patterns:
  01-langgraph           — Multi-agent orchestration
  02-human-in-the-loop   — Confidence-gated human review
  03-guardrails          — Production guardrail service
  04-mcp-tools           — Tool servers for agents
  05-eval-in-ci          — Evaluation in CI/CD pipelines
  06-async-pipelines     — Celery/Redis for large-scale ingestion
  07-knowledge-graphs    — GraphRAG and Neo4j
  08-document-intelligence — OCR, fax labeling, PDF parsing
""")
