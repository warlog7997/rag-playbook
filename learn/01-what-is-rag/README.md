# Chapter 1 — What is RAG?

## The Problem RAG Solves

You have an LLM that knows everything about the world up to its training cutoff.
But it knows nothing about *your* product, *your* docs, *your* codebase.

Ask Claude "How do I reset my password in NovaDash?" — it will either say it doesn't know,
or worse, make something up.

RAG fixes this by giving the LLM an open-book exam instead of a closed one.

---

## The 3-Step Pipeline

```
Your Question
     │
     ▼
[1. INDEX]  ──── Your docs are embedded into vectors and stored in ChromaDB
     │            (done once, at ingest time)
     │
     ▼
[2. RETRIEVE] ── Your question is embedded, similar chunks are fetched
     │
     ▼
[3. GENERATE] ── Claude reads the chunks + your question → answers it
     │
     ▼
  Answer (grounded in your actual docs)
```

---

## What This Demo Does

We have 10 markdown files documenting a fictional SaaS product called **NovaDash**.
The demo:
1. Takes a question about NovaDash
2. Finds the most relevant section from the docs
3. Asks Claude to answer using only that section

Run it:
```bash
# First, ingest the docs (only needed once)
cd learn/
python ingest.py

# Then run the demo
cd 01-what-is-rag/
python demo.py
```

---

## What You'll Notice

- The answer is grounded in the actual docs — no hallucination
- Change the question to something not in the docs → it says "I don't know"
- The quality of retrieval directly affects answer quality

---

## Key Concepts

### Embeddings

An embedding is a dense numerical vector (list of numbers) that represents the *meaning* of a
piece of text. Similar meanings → similar vectors → small geometric distance.

`all-MiniLM-L6-v2` produces 384-dimensional vectors. A single sentence becomes a point in
384-dimensional space. Semantically similar sentences end up near each other.

### Vector Database (ChromaDB)

ChromaDB stores text chunks alongside their embedding vectors. When you query it with a new
embedding, it finds the stored vectors nearest to your query vector using approximate nearest
neighbor search (ANN).

We use ChromaDB's local persistent mode — all data lives on disk in `data/chromadb/`.
No server required.

### Context Window Stuffing

RAG is essentially "context window stuffing with a search filter." Instead of putting your
entire knowledge base into the prompt (impractical for large docs, expensive, slow), you
retrieve only the most relevant 3-5 chunks and put those in the prompt.

---

## Limitations of This Simple Approach

The demo in this chapter uses only **naive vector search** — semantic similarity only.
It works well when the user's question uses similar words to the docs.

It breaks when:
- The user says "cancel" but the docs say "subscription termination"
- The user says "password reset" but the docs say "account recovery"
- The question spans multiple sections

**Next:** [Chapter 2 →](../02-wrong-answers/) — What happens when retrieval fails?
