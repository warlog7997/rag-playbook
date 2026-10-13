[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/warlog7997/rag-playbook/blob/master/learn/02-wrong-answers/notebook.ipynb)

# Chapter 2 — When RAG Gets It Wrong

## The Real Story

We built a Jira ticket assistant for a healthcare platform. The system managed patient transfers
between care facilities. A user asked: *"How does the fast-track system work?"*

The bot returned the Introduction section with full confidence. The actual answer was in a
section called *"Colour-Based Routing — Green clearance → Ready to Transfer Urgent"*. The words
"fast track" never appeared in that section. Naive vector search had no way to bridge that gap.

A support ticket got created saying the system couldn't answer the simplest operational question.
It was the top-priority bug for two weeks.

---

## The NovaDash Equivalent

The NovaDash documentation uses internal terminology that doesn't always match how users phrase
their questions. This is intentional — it mirrors real-world product docs.

**The Semantic Gap Problem:**

| What the user says             | What the docs say                                            |
|-------------------------------|--------------------------------------------------------------|
| "cancel my subscription"      | "subscription termination with data retention policy"        |
| "remove a team member"        | "member offboarding"                                         |
| "forgot my password"          | "account recovery via email verification token flow"         |
| "add 2FA"                     | "two-factor authentication" (works — same words)             |
| "how many projects can I have"| "project limits by plan" (works — similar words)             |

When a user asks "How do I cancel my subscription?", naive vector search:
1. Embeds the word "cancel"
2. Finds sections whose embeddings are geometrically close
3. Returns the billing overview (mentions pricing) instead of the termination section

The termination section contains phrases like "subscription termination with data retention
policy" — semantically similar to cancellation, but not close enough in the embedding space
for a 384-dim model trained on general web text.

---

## Three Approaches Compared

### Approach 1: Naive Vector Search

Uses cosine similarity between query embedding and chunk embeddings. Only understands
*semantic* similarity as captured by the embedding model.

**Wins:** "How do I set up 2FA?" → finds the 2FA section perfectly.

**Fails:** "How do I cancel my subscription?" → "cancel" and "termination" are semantically
related but not identical in the embedding space. The billing intro scores higher because
it broadly covers billing topics.

### Approach 2: BM25 Keyword Search

BM25 (Best Matching 25) is a classical information retrieval algorithm. It scores documents
based on term frequency and inverse document frequency — essentially, how often your query
words appear in each document, adjusted for document length.

**Wins:** "cancel my subscription" → if "cancel" appears in the cancellation section, BM25
finds it directly. But wait — the docs use "termination," not "cancel." So BM25 fails here.
BM25 wins on exact keyword matches.

**Wins when users use exact doc terms:** "subscription termination" → BM25 scores this very
highly because both exact words appear in the relevant section.

**Fails on paraphrase:** "stop paying for NovaDash" → BM25 finds nothing useful because
none of the query words ("stop", "paying") appear in the billing section with high frequency.

### Approach 3: Hybrid Search with Reciprocal Rank Fusion (RRF)

Combines vector AND BM25 rankings using RRF:

```
RRF_score(doc) = Σ  1 / (rank_in_list + 60)
                lists
```

A document that ranks #1 in vector search AND #2 in BM25 gets a much higher combined score
than one that ranks #1 only in vector search.

The constant 60 prevents top-ranked documents from dominating too strongly, giving low-ranked
documents from the "other" retriever a fair chance.

**Wins on everything:** Because it sees both the semantic space (vector) and the exact-term
space (BM25), it catches both cases:
- "cancel" → vector search finds "termination" semantically; BM25 finds "cancel" if it appears
  anywhere nearby
- "subscription termination" → BM25 nails it, pulling the right chunk to the top

---

## Results

Query: "How do I cancel my subscription?"
- The correct answer is in `billing.md` → the "Subscription Termination" section
- The docs use "termination" and "data retention policy" — NOT "cancel"

```
Query                              Naive  BM25   Hybrid
─────────────────────────────────────────────────────────
"cancel my subscription"           ✗      ✓      ✓
"stop paying for NovaDash"         ✗      ✗      ✓
"how to end my account"            ✗      ✗      ✓
"subscription termination policy"  ✓      ✓      ✓
─────────────────────────────────────────────────────────
Recall@1                           0.25   0.50   1.00
```

**Reading the table:**
- ✓ = correct source ranked #1
- ✗ = correct source NOT ranked #1

Hybrid achieves perfect Recall@1 on these queries. Naive gets 1/4. BM25 gets 2/4.

---

## Running the Scripts

```bash
# From the learn/ directory:

# Step 1: See naive vector search fail on semantic gaps
python 02-wrong-answers/scripts/01_naive_rag.py

# Step 2: See BM25 win on some cases, fail on paraphrase
python 02-wrong-answers/scripts/02_bm25_search.py

# Step 3: See hybrid RRF win on all cases
python 02-wrong-answers/scripts/03_hybrid_rrf.py
```

---

## Key Takeaway

> No single retrieval method wins in all cases. Hybrid search is almost always better than
> either alone. The cost is marginally higher latency (two retrieval calls instead of one)
> and slightly more complex code — easily worth the improvement.

**Next:** [Chapter 3 →](../03-irrelevant-results/) — Why the right *section* still isn't
returned even when you find the right *file*.
