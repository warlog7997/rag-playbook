# Production 02 — Human-in-the-Loop

## What is Human-in-the-Loop?

Human-in-the-loop (HITL) is the design pattern of inserting human judgment at
specific points in an AI pipeline — not as a fallback for failures, but as an
intentional architectural choice.

The key insight: **not all AI decisions should be fully autonomous**, especially
when mistakes are expensive to reverse.

Human-in-the-loop systems sit on a spectrum:
```
Fully Automated ←──────────────────────────────→ Human Assisted
   (AI decides everything)                (AI suggests, human decides)

  "Auto-send email"        "Draft email,       "Show me the raw
  when task overdue         human approves"      data only"
```

Good HITL design places the human exactly where their judgment adds the most value —
not at every step (too slow) and not at no steps (too risky).

---

## The Real Story

The V2 migration tool required human approval at **every phase** of the pipeline.
This was not a limitation — it was an intentional design decision.

Here's why:

**Phase 1 → 2 (Discovery → Planning):** The discovery agent identified 400+ PHP files
and their dependencies. Before the planner could proceed, a human needed to verify:
"Did it find all the files? Did it correctly identify the service boundaries?"
If planning started from an incomplete discovery, the entire migration would be wrong.

**Phase 3 → 4 (Review → Generation):** The reviewer could miss logical errors
in the migration plan. A human engineer reviewed the plan before 400+ files were
re-generated — catching architectural issues before they were baked into code.

**Phase 6 → 7 (Validation → Production Flip):** No AI system should deploy to
production without a human signing off. Full stop.

The human approval gates added 30-60 minutes of human time across a 6-8 hour pipeline.
That was a completely acceptable trade-off for the confidence it provided.

---

## Three Patterns for HITL

### Pattern 1: Confidence-Gated Review

The AI generates a confidence score with each decision. Low confidence → human review.
High confidence → proceed automatically.

```python
def route_by_confidence(state: dict) -> str:
    score = state["confidence_score"]
    if score >= 0.85:
        return "auto_approve"
    elif score >= 0.60:
        return "human_review"
    else:
        return "reject_and_explain"
```

**Used in:** Healthcare Jira assistant. Patient transfer tickets with low confidence
scores were routed to a pharmacist queue before any action was taken.

**Trade-off:** You need calibrated confidence scores. LLM self-reported confidence
is often miscalibrated. Use a separate judge model for better calibration.

### Pattern 2: Explicit Approval Gates

The pipeline pauses at defined checkpoints and waits for a human to explicitly
approve before proceeding. No AI self-assessment involved.

```python
# LangGraph interrupt pattern
from langgraph.checkpoint import MemorySaver
from langgraph.graph import interrupt

def review_gate_node(state: dict) -> dict:
    # This suspends execution and waits for human input
    human_decision = interrupt({
        "message": "Review the migration plan",
        "plan": state["migration_plan"],
    })
    return {**state, "human_approved": human_decision["approved"]}
```

**Used in:** V2 migration tool. Every phase transition required explicit approval.
The CLI showed the plan, asked "Approve? (y/N)", and waited.

**Trade-off:** Requires someone to be available. Not suitable for fully automated
24/7 systems where humans can't be in the loop.

### Pattern 3: Correction Flows

The human doesn't just approve/reject — they correct. The AI shows its work,
the human edits the output, and the corrected output flows into the next stage.

```python
def human_correction_node(state: dict) -> dict:
    print("Generated migration plan:")
    print(state["migration_plan"])

    corrected = open_editor_for_correction(state["migration_plan"])

    return {**state, "migration_plan": corrected, "human_reviewed": True}
```

**Used in:** The V2 migration reviewer could suggest changes to the generated code.
Engineers often made small adjustments — adding a missing null check, renaming a
variable for clarity — before passing to the validator.

---

## When NOT to Use Human-in-the-Loop

HITL adds latency and operational cost. Avoid it when:
- The decision is easily reversible (e.g., sending a Slack notification)
- The AI confidence is consistently high (>95%) on a well-understood problem
- The volume is too high for humans to review (millions of transactions/day)
- You've evaluated extensively and the error rate is acceptable for the risk

Use HITL when:
- The decision has significant downstream consequences (code deployment, patient care)
- Confidence is variable and you can't predict which decisions are risky
- You're still building trust in the system (early deployment phase)
- Regulatory requirements mandate human oversight (healthcare, finance)

---

## Coming Soon

Full implementation covering:
- LangGraph interrupt points with a CLI approval interface
- Confidence-gated routing with a calibrated judge model
- Correction flow with a rich terminal editor
- Audit trail: every human decision logged with timestamp and reviewer
- Escalation: unreviewed items auto-escalate after N minutes

**Prerequisites:** `pip install langgraph langchain-anthropic`
