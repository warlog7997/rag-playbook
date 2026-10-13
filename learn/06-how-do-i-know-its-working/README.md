[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/warlog7997/rag-playbook/blob/master/learn/06-how-do-i-know-its-working/notebook.ipynb)

# Chapter 6 — How Do I Know It's Working?

## The Real Story

After building 6 phases of RAG improvements — hybrid search, reranking, contextual
embeddings, multi-query, guardrails — we ran formal evaluation on the healthcare
assistant. The results were humbling.

**The finding that changed everything:** Hybrid search beat Naive by 20% on Recall@1.
But Contextual Embeddings only added marginal improvement over Hybrid. We had spent
significant time on contextual embeddings optimization and the payoff was minimal.

The bottleneck wasn't reranking or embedding quality. It was **retrieval** — specifically,
the semantic gap problem we addressed in Chapter 2. Fixing that first with hybrid search
was the right call. Everything else was incremental.

This is why formal evaluation matters. Without numbers, you're optimizing by intuition.
With numbers, you know exactly where the leverage is.

---

## The Metrics That Matter

### Recall@K

*"In the top K retrieved chunks, did the correct answer appear?"*

- **Recall@1**: Correct chunk is ranked #1. Most important — if users only read the top result.
- **Recall@3**: Correct chunk is in the top 3. Reasonable for LLM synthesis (reads all 3).
- **Recall@5**: Correct chunk is in the top 5. Upper bound of typical fetch size.

```
Recall@1 = (# questions where correct chunk is rank 1) / (total questions)
```

### MRR (Mean Reciprocal Rank)

*"On average, where does the correct chunk appear?"*

```
MRR = (1/N) * Σ  1 / rank(correct chunk)
              N
```

If the correct chunk is always at rank 1: MRR = 1.0
If always at rank 2: MRR = 0.5
If always at rank 3: MRR = 0.33

MRR is more nuanced than Recall@K — a system that consistently ranks the correct
answer #2 (MRR=0.5) is better than one that sometimes gets rank 1 and sometimes
rank 10 (lower MRR despite same Recall@3).

---

## Results from the Real System (Adapted)

These numbers are adapted from the SIPA v2 healthcare assistant evaluation,
applied to the NovaDash knowledge base structure:

```
Phase               Recall@1  Recall@3  Recall@5   MRR
─────────────────────────────────────────────────────
Naive (Vector)        0.30      0.60      0.80    0.508
Hybrid (RRF)          0.50      0.70      0.90    0.628
Contextual            0.50      0.70      0.90    0.650
```

**Key observations:**
- Hybrid added +20% Recall@1 and +0.12 MRR over Naive. Huge win.
- Contextual added 0% Recall@1 and +0.022 MRR over Hybrid. Marginal.
- The lesson: fixing semantic gap retrieval (hybrid) was the highest-leverage change.

**The bottleneck insight:** "Good reranking on bad retrieval still gives bad answers.
Fix retrieval first. Then optimize everything else."

---

## Types of Evaluation

### Retrieval Metrics (Scripts 01, 02)
Measure how often the correct document chunk is retrieved.
- Requires a ground-truth dataset of (question, correct_chunk) pairs.
- Does NOT require an LLM — pure ranking comparison.

### LLM Judge (Script 03)
Measure the quality of the generated answer.
- Faithfulness: Does the answer stick to the retrieved context?
- Relevance: Does the answer address the question?
- Completeness: Does the answer cover all aspects?
- Requires an LLM as judge (we use Haiku for speed/cost).

### RAGAS (Script 04)
An open-source RAG evaluation framework that computes:
- **Context Precision**: Of the retrieved chunks, what fraction were actually useful?
- **Context Recall**: Of all the useful chunks that exist, what fraction were retrieved?
- **Faithfulness**: Does the answer contradict the retrieved context?
- **Answer Relevancy**: Is the answer relevant to the question asked?

---

## Running the Scripts

```bash
# From the learn/ directory:

# Step 1: Build an evaluation dataset (with semantic gaps built in)
python 06-how-do-i-know-its-working/scripts/01_build_eval_dataset.py

# Step 2: Recall@K and MRR comparison (naive vs hybrid)
python 06-how-do-i-know-its-working/scripts/02_recall_mrr.py

# Step 3: LLM judge — score generated answers for quality
python 06-how-do-i-know-its-working/scripts/03_llm_judge.py

# Step 4: RAGAS evaluation (requires ragas package)
python 06-how-do-i-know-its-working/scripts/04_ragas_eval.py
```

---

## Building a Good Eval Dataset

The evaluation dataset is everything. Bad eval = misleading results.

**Rules for building good eval questions:**
1. **Use different words than the docs** — test semantic search, not keyword matching
2. **Include all semantic gap cases** — "cancel" when docs say "terminate"
3. **Include easy questions too** — to ensure you haven't broken basic cases
4. **Specify the exact source section** — so you can verify retrieval precisely
5. **Generate with LLM, validate manually** — Claude Sonnet generates diverse questions,
   but a human should spot-check the answers

We build the dataset by asking Claude Sonnet to read each doc section and generate
questions that a real user might ask — using different phrasing than the docs.

---

## Key Takeaway

> Measurement is the only way to know if your RAG system is improving.
> Run eval before AND after every change. If a change doesn't improve the numbers,
> it didn't improve the system — regardless of how clever it seemed.

**You've completed the learning track.**
**Next:** [Production →](../../production/) — Advanced patterns for production deployment.
