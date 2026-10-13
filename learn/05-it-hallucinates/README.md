# Chapter 5 — It Hallucinates

## The Real Story

Our healthcare Jira assistant started inventing PHP function names and database columns
that didn't exist. A pharmacist reported: *"The bot told me to call the `fastTrackPatient()`
method — that method doesn't exist anywhere in the codebase."*

It was hallucinating code that *sounded* plausible. The function name was consistent with
the naming convention we used, the parameters made logical sense, and the description was
accurate — but the function simply didn't exist. The LLM was pattern-completing based on
what it had seen in the retrieved chunks, filling gaps with invented details.

After fixing retrieval and adding a reranker, we thought we were done. We weren't.
Hallucination is a separate problem from retrieval quality.

---

## The NovaDash Equivalent

The NovaDash docs describe the REST API at `https://api.novadash.io/v2`. When asked
questions like *"How do I pause my subscription?"*, the bot would sometimes respond:

> "You can pause your subscription via the API: `POST /api/v2/subscription/pause`
> with `{"duration": "30_days"}` in the request body."

That endpoint **does not exist**. NovaDash has no "pause" feature — only termination.
But the endpoint URL, the request format, and the explanation all looked perfectly reasonable.

This is the most dangerous kind of hallucination: confident, plausible, and wrong.

---

## Four Defenses Against Hallucination

### Defense 1: Grounding Prompts

The simplest fix. Add explicit instructions to the system prompt that constrain the model
to the provided context:

```
BAD:  "Answer questions about NovaDash."
GOOD: "Answer using ONLY the documentation provided. If the answer isn't in the
       context, say 'I don't have enough information.' Never invent endpoints,
       features, or procedures not explicitly mentioned in the docs."
```

This doesn't eliminate hallucination but dramatically reduces it. The model still
occasionally violates the instruction for very confident-seeming false information.

### Defense 2: Citation Enforcement

Force the model to cite every claim using a structured format:
```
[billing.md::subscription_termination_with_data_retention_policy]
```

Then:
1. Parse citations from the response using regex
2. Verify each citation exists in the knowledge base
3. Flag responses with invented citations

If the model cites `[billing.md::pause_subscription]` and that chunk ID doesn't exist
in your index, the response is flagged as potentially hallucinated.

### Defense 3: Confidence Scoring

After generating an answer, ask a second (cheaper) model to evaluate:
```json
{"confidence": 8, "missing_info": "exact retry intervals", "quality": "good"}
```

Low confidence + "poor" quality triggers a fallback: tell the user "I'm not certain
about this — please verify with the official docs or contact support."

### Defense 4: Full Guardrail Stack

A production system needs multiple layers:
1. **Prompt injection detection**: catch "ignore previous instructions"
2. **Off-topic detection**: catch questions about unrelated topics
3. **PII detection**: prevent the bot from leaking email addresses or SSNs from docs
4. **Citation verification**: catch invented citations
5. **Confidence gate**: route low-confidence responses to human review

---

## Running the Scripts

```bash
# From the learn/ directory:

# Defense 1: Compare with/without grounding prompts
python 05-it-hallucinates/scripts/01_grounding_prompts.py

# Defense 2: Citation enforcement and verification
python 05-it-hallucinates/scripts/02_citation.py

# Defense 3: Confidence scoring
python 05-it-hallucinates/scripts/03_confidence_scoring.py

# Defense 4: Full guardrail stack
python 05-it-hallucinates/scripts/04_guardrails.py
```

---

## The Uncomfortable Truth

Even with all four defenses:
- Grounding prompts reduce hallucination but don't eliminate it
- Citation verification catches invented references, not subtle factual errors
- Confidence scoring is itself an LLM call that can hallucinate
- Guardrails add latency and cost

In production, the right posture is:
1. Make hallucinations obvious (citations point to source)
2. Gate low-confidence responses (don't let the bot guess)
3. Tell users explicitly: "This bot may make mistakes — verify important information"
4. Log and review every low-confidence response manually at first

---

## Key Takeaway

> Perfect retrieval does not prevent hallucination. The model will always try to
> fill gaps in the context with plausible-sounding information. Defense-in-depth
> with grounding + citations + confidence scoring is the right approach.

**Next:** [Chapter 6 →](../06-how-do-i-know-its-working/) — How to formally evaluate
whether your RAG system is actually working.
