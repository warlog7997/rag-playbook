# Production 05 — Evaluation in CI/CD

## What is Eval-in-CI?

Running your RAG evaluation suite automatically on every code change —
as part of your CI/CD pipeline — before any deployment.

Just like unit tests catch regressions in application logic, eval-in-CI catches
regressions in AI system quality. A prompt change that improves one query may
silently break three others. Without automated evaluation, you won't know until
a user reports it.

---

## The Real Story

Without eval-in-CI, this happened: a well-intentioned prompt change was made to
improve the formatting of the healthcare assistant's responses. The change was
deployed. Three days later, a user reported that queries about "SSO configuration"
were now returning billing information instead.

The prompt change had subtly shifted how the system handled technical terminology —
making it overly conservative about returning domain-specific content. Three queries
that previously scored 9/10 now scored 3/10. Nobody noticed because there was no
automated check.

Adding eval-in-CI as a GitHub Actions workflow caught this category of regression
immediately. The PR that caused the issue would have been blocked at the gate with:

```
❌ RAG Eval Failed
  context_recall dropped from 0.78 → 0.61 (threshold: 0.70)
  Failing queries:
    - "How do I configure SSO with Okta?"  [was: 0.92, now: 0.41]
    - "What is identity provider binding?"  [was: 0.88, now: 0.38]
    - "SAML setup steps"                   [was: 0.85, now: 0.44]
```

---

## The Eval-in-CI Architecture

```
Git Push / PR
     │
     ▼
GitHub Actions Workflow
     │
     ├── Step 1: Install dependencies
     ├── Step 2: Load golden dataset (data/eval_dataset.json)
     ├── Step 3: Run retrieval eval → Recall@1, MRR
     ├── Step 4: Run answer quality eval → LLM judge scores
     ├── Step 5: Compare against thresholds
     │              ↓
     │         All metrics within thresholds → ✓ PASS
     │         Any metric below threshold   → ✗ FAIL (block merge)
     └── Step 6: Publish results as PR comment
```

---

## GitHub Actions Workflow

```yaml
name: RAG Evaluation

on:
  pull_request:
    paths:
      - 'learn/**'
      - 'knowledge-base/**'
      - 'requirements.txt'

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run ingest
        run: cd learn && python ingest.py
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

      - name: Run retrieval evaluation
        run: python learn/06-how-do-i-know-its-working/scripts/02_recall_mrr.py
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

      - name: Check thresholds
        run: python ci/check_thresholds.py
        env:
          RECALL_AT_1_THRESHOLD: 0.45
          MRR_THRESHOLD: 0.60
```

---

## Threshold Configuration

```python
# ci/check_thresholds.py
THRESHOLDS = {
    "recall_at_1": float(os.getenv("RECALL_AT_1_THRESHOLD", 0.45)),
    "recall_at_3": float(os.getenv("RECALL_AT_3_THRESHOLD", 0.65)),
    "mrr": float(os.getenv("MRR_THRESHOLD", 0.60)),
    "faithfulness": float(os.getenv("FAITHFULNESS_THRESHOLD", 0.80)),
}
```

Setting thresholds:
- Start with 10-20% below your current baseline (not too strict at first)
- Tighten them as your system matures
- Never set a threshold higher than current performance (that blocks all PRs)
- Use separate thresholds for different question categories (easy vs hard)

---

## Golden Dataset Management

The eval dataset (`data/eval_dataset.json`) is the most important asset in eval-in-CI.

**It must be committed to git.** Without a stable, versioned eval dataset:
- Your CI results are not reproducible
- You can't tell if a metric change is due to your code change or the dataset changing

**It must be updated when the docs change.** If you add a new knowledge base section,
add eval questions for it. If you deprecate a feature, remove or update its eval questions.

**Treat it like a test suite.** PRs that change the knowledge base should include
updates to the eval dataset. Require this in code review.

---

## Coming Soon

Full implementation covering:
- GitHub Actions workflow with complete eval pipeline
- `ci/check_thresholds.py` with configurable thresholds
- PR comment reporter (posts eval results as a PR comment)
- Baseline comparison (compares against main branch, not just absolute thresholds)
- Slack alert on CI eval failure
- Eval result trending dashboard

**Prerequisites:** GitHub Actions, `pip install ragas langchain-anthropic`
