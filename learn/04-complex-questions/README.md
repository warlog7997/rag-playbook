# Chapter 4 — Complex Questions

## The Real Story

Our hardest test query for the healthcare Jira assistant was:
*"How does the fast-track system work?"*

Every technique we built in Phases 1-6 — hybrid search, reranking, contextual embeddings —
failed this query. The answer wasn't in one section. It required synthesizing information
from the triage protocol, the colour-coded routing system, the transfer-ready criteria,
and the escalation procedures. No single chunk contained "the answer."

Phase 7 — **Agentic RAG with a ReAct loop** — was the FIRST approach to answer this
correctly. The agent searched 3 times, each with a more targeted query, before finding
all the relevant sections. Then it synthesized a coherent answer from the combined context.

This was a pivotal moment in the project. We understood that for domain expert questions,
the right approach is an agent that *reasons about what to search for*, not just a pipeline
that searches once.

---

## The NovaDash Equivalent

**The hard query:**
> "Compare how Free and Pro plans handle user limits, project limits, and what happens
> when you exceed those limits."

**Why single-query RAG fails:**
- This question requires information from at least 3 files: `billing.md`, `projects.md`,
  and `user-management.md`
- A single query about "user limits" returns chunks from user-management
- A single query about "project limits" returns chunks from projects
- A single query about "exceeding limits" returns chunks about plan restrictions
- No single query retrieves all three relevant sections

Single-query RAG with top-3 chunks either:
1. Returns only one aspect and ignores the others
2. Returns generic billing overview instead of the specific limit details

---

## Three Approaches to Complex Questions

### Approach 1: Multi-Query (Query Expansion)

Generate 4 different phrasings of the same question and run them all.

```
Original: "Compare Free and Pro plan limits"
Expanded to:
  1. "Free plan user and project limits"
  2. "Pro plan features and restrictions"
  3. "What happens when you exceed plan limits"
  4. "Plan comparison user seats projects storage"
```

Each query fetches 5 chunks. After deduplication, you have ~15-18 unique chunks covering
all aspects. Better coverage — but the final context is larger and may be noisier.

**When to use:** Broad, multi-faceted questions where you want comprehensive coverage.

### Approach 2: Query Decomposition

Break the question into focused sub-questions and answer each separately, then combine.

```
Original: "Compare Free and Pro plan user limits and what happens when exceeded"
Decomposed:
  Sub-Q1: "What are the user limits on the Free plan?"
  Sub-Q2: "What are the user limits on the Pro plan?"
  Sub-Q3: "What happens when you exceed the user limit on Free?"
```

Each sub-question gets its own retrieval + generation step. The final answer combines
three focused answers.

**Advantage over multi-query:** Each sub-question gets a dedicated answer, so the final
answer is structured and directly addresses each part. Better for "compare X and Y" questions.

### Approach 3: Agentic RAG (ReAct Loop)

Give Claude a `search` tool and let it decide:
1. What to search for
2. Whether it has enough information
3. Whether it needs to search again

```
Iteration 1: Claude searches "Free plan limits" → reads results
             Thinks: "I have user limits but need project limits"
Iteration 2: Claude searches "project limits by plan" → reads results
             Thinks: "I need to know what happens when limits are exceeded"
Iteration 3: Claude searches "exceeding plan limits" → reads results
             Thinks: "I now have everything I need"
Final: Claude synthesizes all gathered context into a comprehensive answer
```

**The ReAct pattern:**
```
Thought → Action (search) → Observation (results) → Thought → ... → Final Answer
```

This is the most powerful approach because the agent *adapts* its search strategy based on
what it finds. It's also the most expensive (multiple API calls) and slowest.

**When to use:** Complex multi-part questions, or any question where you don't know in
advance how many searches are needed.

---

## Running the Scripts

```bash
# From the learn/ directory:

# Approach 1: Multi-query expansion (fastest)
python 04-complex-questions/scripts/01_multi_query.py

# Approach 2: Query decomposition (structured answers)
python 04-complex-questions/scripts/02_query_decomposition.py

# Approach 3: Agentic ReAct loop (most powerful)
python 04-complex-questions/scripts/03_agentic_react.py
```

---

## The Real Trade-off

| Approach         | Queries | API Calls | Latency  | Quality   | Best for              |
|-----------------|---------|-----------|----------|-----------|-----------------------|
| Single query     | 1       | 1         | ~1s      | Poor      | Simple factual Q&A    |
| Multi-query      | 4       | 1+        | ~2s      | Good      | Broad coverage        |
| Decomposition    | 2-3     | 3-4       | ~4s      | Very good | Compare/contrast      |
| Agentic ReAct    | 2-5     | 5-10      | ~8-15s   | Excellent | Anything complex      |

For a support chatbot: single-query is fine for most questions.
For a research assistant: agentic ReAct is worth the latency.

---

## Key Takeaway

> For questions that span multiple topics, a single-pass RAG pipeline will always
> miss part of the answer. Multi-query, decomposition, and agentic approaches each
> trade speed and complexity for completeness. Start simple — upgrade to agentic only
> when the query complexity demands it.

**Next:** [Chapter 5 →](../05-it-hallucinates/) — Even good retrieval can produce
hallucinated answers. How to detect and prevent it.
