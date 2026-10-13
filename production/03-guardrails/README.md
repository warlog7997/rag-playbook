# Production 03 — Guardrail Service

## What is a Guardrail Service?

In the learning track (Chapter 5), you built guardrail functions as standalone scripts.
In production, guardrails are deployed as a **dedicated service** — a FastAPI microservice
that every AI pipeline routes through before and after generating a response.

This separation matters for several reasons:
- **Centralization**: All AI systems in your stack use the same guardrails
- **Maintainability**: Update injection patterns or PII regexes in one place
- **Observability**: Every flagged request is logged and auditable
- **Performance**: Regex checks are synchronous; LLM checks run in parallel
- **Versioning**: Guardrail rules can be versioned independently of the AI system

---

## The Real Story

The healthcare Jira assistant needed strict guardrails from day one. The system
had access to patient transfer information — real names, MRN numbers, medication details.
PHI (Protected Health Information) could not leave the system in any response.

We built a four-layer guardrail pipeline:

**Layer 1 — Regex Fast-Path (synchronous, <1ms)**
Catches prompt injections, PII patterns, known jailbreak phrases. These are cheap and
should never reach the LLM. If a pattern matches, the request is rejected before any API
call is made.

**Layer 2 — LLM Semantic Check (async, ~300ms)**
Asks Claude Haiku: "Is this question about our healthcare platform, or is it an
out-of-scope request?" Catches things regex can't — subtle off-topic requests, semantic
jailbreaks, questions designed to extract training data.

**Layer 3 — Response Scanner (regex, synchronous)**
After generating the answer, scan it for PII patterns: names that look like MRNs,
phone number patterns, email addresses. The model occasionally echoed back patient
data from retrieved context — this layer caught it.

**Layer 4 — Citation Verifier**
Verify that every cited source exists in the knowledge base. An invented citation is
a strong hallucination signal. Log it and flag the response for manual review.

---

## Production Architecture

```
Client Request
     │
     ▼
[Guardrail Service] ── Layer 1: Regex (sync)
     │                          ↓
     │                Layer 2: Semantic check (async)
     │                          ↓
     │                If blocked → 403 response
     ▼
[RAG Pipeline] ── retrieve → generate
     │
     ▼
[Guardrail Service] ── Layer 3: Response scanner (sync)
     │                          ↓
     │                Layer 4: Citation verifier (async)
     │                          ↓
     │                If flagged → log + low-confidence flag
     ▼
Final Response to Client
```

The guardrail service is stateless and horizontally scalable. Each instance handles
one request at a time with no shared state.

---

## API Design

```python
POST /guardrails/check-input
{
  "query": "How do I reset my password?",
  "session_id": "sess_abc123",
  "user_id": "usr_xyz789"
}
Response: {"passed": true, "flags": [], "request_id": "req_001"}

POST /guardrails/check-output
{
  "query": "...",
  "response": "...",
  "citations": ["billing.md::termination"],
  "request_id": "req_001"
}
Response: {"passed": true, "flags": [], "confidence": 0.92}
```

---

## Monitoring and Alerting

Every blocked request is written to a structured log:
```json
{
  "timestamp": "2024-11-15T14:32:00Z",
  "request_id": "req_001",
  "blocked_at": "layer_1_regex",
  "pattern_matched": "ignore previous instructions",
  "user_id": "usr_xyz789",
  "session_id": "sess_abc123",
  "query_hash": "sha256:...",
  "action": "rejected"
}
```

Alerts fire when:
- >5% of requests blocked in a 5-minute window (potential attack)
- PII detected in response (immediate alert — potential HIPAA violation)
- Citation verification failure rate >10% (retrieval quality degradation)

---

## Coming Soon

Full implementation covering:
- FastAPI guardrail service with all 4 layers
- Async parallel execution of LLM-based checks
- Structured logging with correlation IDs
- Health check endpoints
- Docker container configuration
- Rate limiting per user/session
- Admin dashboard for reviewing flagged requests

See Chapter 5 learn scripts for the core guardrail logic this service wraps.
