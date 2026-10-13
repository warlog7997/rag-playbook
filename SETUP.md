# Setup Guide

Get the RAG Playbook running in under 10 minutes.

---

## Prerequisites

- Python 3.11 or higher
- An Anthropic API key ([get one here](https://console.anthropic.com/))

---

## Step 1: Clone the Repo

```bash
git clone https://github.com/your-username/rag-playbook.git
cd rag-playbook
```

---

## Step 2: Create a Virtual Environment

```bash
python -m venv .venv

# Activate it:
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

---

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `anthropic` — Claude API client
- `chromadb` — local vector database
- `sentence-transformers` — embedding model
- `rank-bm25` — BM25 keyword search
- `keyring` — secure API key storage
- All other dependencies for advanced modules

The first run will also download the `all-MiniLM-L6-v2` embedding model
(~90 MB) from Hugging Face when you first run a script.

---

## Step 4: Set Up Your API Key

NovaDash uses the system keyring to store your Anthropic API key securely.
Run this once:

```python
import keyring
keyring.set_password("Anthorpic", "API_KEY", "your-key-here")
```

Note the intentional spelling "Anthorpic" (not "Anthropic") — this is how the
key is stored across all scripts in this repo. Copy the spelling exactly.

To verify it's set:
```python
import keyring
print(keyring.get_password("Anthorpic", "API_KEY"))
```

---

## Step 5: Ingest the Knowledge Base

This runs once to embed all NovaDash documentation into ChromaDB and build the BM25 index.

```bash
cd learn
python ingest.py
```

Expected output:
```
=== Ingesting NovaDash Knowledge Base ===

Loaded 87 chunks from .../knowledge-base

Loading embedding model...
Embedding 87 chunks...
100%|██████████| 87/87 [00:12<00:00,  7.25it/s]
ChromaDB: 87 chunks stored in 'novadash_docs'
BM25: index saved to .../data/bm25_index.pkl

Done! Run any script in learn/ now.
```

---

## Step 6: Run Chapter 1

```bash
cd learn/01-what-is-rag
python demo.py
```

You should see the question answered correctly using the NovaDash docs.

---

## Working Through the Chapters

```bash
# Chapter 1: Basic RAG
cd learn/01-what-is-rag
python demo.py

# Chapter 2: Why naive RAG fails
cd learn/02-wrong-answers
python scripts/01_naive_rag.py
python scripts/02_bm25_search.py
python scripts/03_hybrid_rrf.py

# Chapter 3: Reranking
cd learn/03-irrelevant-results
python scripts/01_cross_encoder_reranker.py
python scripts/02_llm_reranker.py
python scripts/03_contextual_embeddings.py

# Chapter 4: Complex questions
cd learn/04-complex-questions
python scripts/01_multi_query.py
python scripts/02_query_decomposition.py
python scripts/03_agentic_react.py

# Chapter 5: Hallucination
cd learn/05-it-hallucinates
python scripts/01_grounding_prompts.py
python scripts/02_citation.py
python scripts/03_confidence_scoring.py
python scripts/04_guardrails.py

# Chapter 6: Evaluation
cd learn/06-how-do-i-know-its-working
python scripts/01_build_eval_dataset.py   # Run this first
python scripts/02_recall_mrr.py
python scripts/03_llm_judge.py
python scripts/04_ragas_eval.py           # Requires: pip install ragas
```

---

## Running Scripts from Any Directory

All scripts in `learn/` use:
```python
sys.path.insert(0, str(Path(__file__).parent.parent))
```

This means you can run any script from anywhere:
```bash
# From the repo root:
python learn/01-what-is-rag/demo.py
python learn/02-wrong-answers/scripts/01_naive_rag.py

# From inside a chapter directory:
cd learn/01-what-is-rag
python demo.py
```

---

## Troubleshooting

**"BM25 index not found"**
Run `python learn/ingest.py` first. The index files are created in `data/`.

**"Anthropic API key not found"**
Run `keyring.set_password("Anthorpic", "API_KEY", "your-key")` again.
Note: it's "Anthorpic" not "Anthropic".

**Slow embedding on first run**
The `all-MiniLM-L6-v2` model is ~90 MB and is downloaded once from HuggingFace.
Subsequent runs use the cached model.

**ChromaDB "Collection not found"**
Run `python learn/ingest.py` to rebuild the ChromaDB collection.

**"ModuleNotFoundError: ragas"**
Chapter 6 Script 4 requires RAGAS: `pip install ragas langchain-anthropic`

---

## Cost Estimates

| Script               | API Calls    | Estimated Cost |
|---------------------|--------------|----------------|
| ingest.py            | 0            | Free           |
| Chapter 1 demo       | 1            | ~$0.001        |
| Chapter 2 scripts    | 0            | Free (no LLM)  |
| Chapter 3 scripts    | 15-30        | ~$0.01         |
| Chapter 4 scripts    | 5-15         | ~$0.01         |
| Chapter 5 scripts    | 10-30        | ~$0.02         |
| Chapter 6 (all)      | 100-200      | ~$0.10         |
| **Full playbook**    | ~300-500     | **~$0.25**     |

All estimates use Claude Haiku pricing. The full playbook costs less than a coffee.
