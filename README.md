# RAG Playbook — From Broken to Production-Ready

> **Every chapter starts with a real problem. Every solution comes from real production code.**

This repo documents the complete journey of building RAG systems — from a naive bot that returns garbage answers, all the way to a production agent with evaluation, guardrails, and human-in-the-loop flows.

Every technique here was battle-tested across real AI projects: a healthcare Jira assistant, a prescription sig predictor, a multi-agent code migration tool, and a fax labeling system.

---

## Who is this for?

| You are... | Start here | Run in Colab |
|---|---|---|
| New to RAG, want to understand the basics | [learn/01-what-is-rag](./learn/01-what-is-rag/) | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/warlog7997/rag-playbook/blob/master/learn/01-what-is-rag/notebook.ipynb) |
| Built a RAG bot but it returns wrong answers | [learn/02-wrong-answers](./learn/02-wrong-answers/) | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/warlog7997/rag-playbook/blob/master/learn/02-wrong-answers/notebook.ipynb) |
| Results are retrieved but feel irrelevant | [learn/03-irrelevant-results](./learn/03-irrelevant-results/) | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/warlog7997/rag-playbook/blob/master/learn/03-irrelevant-results/notebook.ipynb) |
| Bot fails on complex, multi-part questions | [learn/04-complex-questions](./learn/04-complex-questions/) | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/warlog7997/rag-playbook/blob/master/learn/04-complex-questions/notebook.ipynb) |
| Bot makes up facts / hallucinates | [learn/05-it-hallucinates](./learn/05-it-hallucinates/) | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/warlog7997/rag-playbook/blob/master/learn/05-it-hallucinates/notebook.ipynb) |
| Can't tell if your RAG is actually working | [learn/06-how-do-i-know-its-working](./learn/06-how-do-i-know-its-working/) | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/warlog7997/rag-playbook/blob/master/learn/06-how-do-i-know-its-working/notebook.ipynb) |
| Building production systems (LangGraph, MCP, etc.) | [production/](./production/) | — |

---

## The Knowledge Base

All examples in this repo use the same **NovaDash SaaS product docs** as the knowledge base — 10 markdown files covering authentication, billing, user management, integrations, and more. Simple enough to understand in 5 minutes, rich enough to trigger real RAG failure modes.

See [knowledge-base/](./knowledge-base/) for the full source.

---

## Learning Track

### The Story

We built a bot that lets developers ask questions about our blog app codebase:

> *"How does a user create a post?"*
> *"What database tables does the comment system touch?"*
> *"How does authentication work?"*

Here's every problem we hit — and how we fixed it.

---

### Chapter 1 — What is RAG?
**[learn/01-what-is-rag/](./learn/01-what-is-rag/)** &nbsp; [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/warlog7997/rag-playbook/blob/master/learn/01-what-is-rag/notebook.ipynb)

The simplest possible RAG system. Embed documents, store in a vector DB, retrieve, generate. Understand the 3-step pipeline before anything else.

**You'll learn:** Embeddings, vector similarity, ChromaDB basics, the generate step.

---

### Chapter 2 — My Bot Returns Wrong Answers
**[learn/02-wrong-answers/](./learn/02-wrong-answers/)**

Your naive RAG retrieves the wrong chunks. The answer is confidently wrong. Here's why — and three progressively better fixes.

**Problem → Fix progression:**
- Naive vector search → fails on exact keywords
- BM25 keyword search → fails on natural language
- Hybrid search (Vector + BM25 + RRF) → best of both worlds ✅

**You'll learn:** BM25, Reciprocal Rank Fusion, when to use each approach.

> *This exact problem appeared in our healthcare Jira assistant. "How does the fast-track system work?" returned the Introduction section, not the routing logic.*

---

### Chapter 3 — Results Are Retrieved But Feel Irrelevant
**[learn/03-irrelevant-results/](./learn/03-irrelevant-results/)**

Your retrieval finds the right documents, but the top results are noisy or off-topic. Reranking fixes this.

**Problem → Fix progression:**
- Cross-encoder reranker → removes noise, domain mismatch issue
- LLM-as-reranker (Claude Haiku) → domain-aware, higher cost
- Contextual embeddings → richer semantic space at ingest time

**You'll learn:** Cross-encoders vs bi-encoders, LLM-as-judge for ranking, contextual ingestion.

---

### Chapter 4 — It Can't Answer Complex Questions
**[learn/04-complex-questions/](./learn/04-complex-questions/)**

Simple questions work fine. But *"Compare how post creation and comment creation handle validation — and which one is missing error handling?"* returns garbage.

**Problem → Fix progression:**
- Multi-query expansion → generates 4 variants, merges results
- Query decomposition → breaks question into sub-questions
- Agentic RAG (ReAct loop) → model decides when to search again ✅

**You'll learn:** HyDE, step-back prompting, ReAct agents, tool use with Claude.

> *Agentic RAG was the first approach that correctly answered our hardest test query end-to-end.*

---

### Chapter 5 — It Hallucinates
**[learn/05-it-hallucinates/](./learn/05-it-hallucinates/)**

The bot invents function names, fabricates database columns, and states things that aren't in the codebase at all.

**Problem → Fix progression:**
- Grounding prompts → force model to cite sources
- Citation back to file + line → verifiable answers
- Confidence scoring → surface uncertainty to the user
- Guardrails → detect and block dangerous outputs

**You'll learn:** Prompt grounding, citation patterns, PII detection, prompt injection defense.

> *We built a full guardrail stack for our healthcare assistant: regex fast-path + Haiku semantic check + response scanning.*

---

### Chapter 6 — How Do I Know It's Actually Working?
**[learn/06-how-do-i-know-its-working/](./learn/06-how-do-i-know-its-working/)**

You've made changes. Is it better or worse? Without metrics you're flying blind.

**What we build:**
- Golden dataset (10 Q&A pairs, generated by Claude)
- Recall@K and MRR metrics
- LLM-as-judge for answer quality
- RAGAS for end-to-end evaluation

**You'll learn:** Eval-driven development, building ground truth datasets, measuring retrieval vs generation quality separately.

> *Our eval revealed that Phase 3 (Hybrid) beat Naive by 20% Recall@1 — but Phases 4-6 only added marginal gains. The bottleneck was retrieval, not reranking.*

---

## Production Track

For engineers building real systems.

| Module | What you'll build |
|---|---|
| [01-langgraph](./production/01-langgraph/) | Multi-node agent graph with state management |
| [02-human-in-the-loop](./production/02-human-in-the-loop/) | Interrupt points, confidence surfacing, correction flows |
| [03-guardrails](./production/03-guardrails/) | Prompt injection, PII, scope enforcement, response scanning |
| [04-mcp-tools](./production/04-mcp-tools/) | MCP tool servers, agent-to-tool protocols |
| [05-eval-in-ci](./production/05-eval-in-ci/) | Golden datasets, regression suites, eval gates in CI |
| [06-async-pipelines](./production/06-async-pipelines/) | Long-running doc ingestion with Celery/Redis |
| [07-knowledge-graphs](./production/07-knowledge-graphs/) | GraphRAG, Neo4j for agent memory |
| [08-document-intelligence](./production/08-document-intelligence/) | OCR, layout-aware PDF parsing, table extraction |

---

## Real Projects Behind This Repo

Every concept here came from building these systems:

| Project | What it taught us |
|---|---|
| **SIPA** (Healthcare Jira Assistant) | Per-method chunking, category routing, guardrail stacks, multi-search |
| **SIPA v2** (RAG Research Lab) | 8-phase RAG progression, eval metrics, why agentic RAG wins |
| **Sig Predictor** | FAISS at 300K records, production FastAPI RAG API |
| **V2 Migration Tool** | Multi-agent orchestration, human approval gates, cost tracking |
| **Fax Labeler** | Document intelligence, OCR, ground truth building for fine-tuning |

---

## Setup

```bash
git clone https://github.com/yourusername/rag-playbook
cd rag-playbook
pip install -r requirements.txt
```

Each module has its own `README.md` with specific setup instructions.

**Core dependencies:**
```
anthropic
chromadb
sentence-transformers
rank-bm25
langsmith
langgraph
langchain-anthropic
ragas
fastapi
```

---

## Contributing

Found a better approach? Hit a problem not covered here? PRs welcome.

Each module follows the same format:
1. State the problem clearly
2. Show why naive approaches fail
3. Show the fix with working code
4. Show evaluation proving it works better

---

## License

MIT
