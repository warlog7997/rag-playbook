# Production 06 — Async Pipelines: Large-Scale Document Ingestion

## The Problem with Synchronous Ingestion

The `ingest.py` script in the learning track is synchronous. For 10 markdown files,
that's fine — it completes in under a minute.

For production workloads, synchronous ingestion breaks down:
- **400+ PHP files** with Claude enrichment per file → 45+ minutes
- **9,000+ healthcare faxes** → hours
- **Enterprise documentation corpus** (10,000+ pages) → overnight jobs

Synchronous ingestion during these workloads:
- Blocks the ingestion process entirely if one item fails
- Can't be monitored or restarted from a failure point
- Can't process multiple items in parallel
- Times out in web request contexts (30-60 second limits)

The solution: **async batch pipelines with Celery and Redis**.

---

## The Real Story

Ingesting 400+ PHP files for the V2 migration tool required Claude Sonnet to analyze
each file: identify what it does, what functions it exports, what it depends on, and
what migration approach makes sense.

At ~15 seconds per file (including the LLM call and error handling), that's 100 minutes
of serial processing. And if file 387 failed due to a rate limit, we'd have to restart
from scratch.

The fix: Celery workers processing files in parallel, with:
- 10 concurrent workers (staying under API rate limits)
- Redis as the task queue and result backend
- Automatic retry on rate limit errors (exponential backoff)
- Progress tracking visible in real time
- Resumable: restart from the last successful point after failure

Processing time dropped from 100 minutes (serial) to 12 minutes (parallel).

---

## Architecture

```
Ingestion Trigger (CLI / API / Cron)
     │
     ▼
[Task Producer] — creates N tasks in Redis queue
     │
     ▼
Redis Queue ──────────────────────────────────────
     │                 │                   │
     ▼                 ▼                   ▼
[Worker 1]        [Worker 2]          [Worker 3]
process_file()    process_file()    process_file()
     │                 │                   │
     ▼                 ▼                   ▼
  ChromaDB         ChromaDB             ChromaDB
  (append)         (append)             (append)
     │
     ▼
[Result Backend (Redis)] — track progress
     │
     ▼
Progress Monitor CLI — shows completion %
```

---

## Key Implementation Patterns

### Rate Limit Handling

```python
from celery import Task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

class RateLimitAwareTask(Task):
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        if "rate_limit" in str(exc).lower() or "429" in str(exc):
            logger.warning(f"Rate limited on {args[0]} — will retry")

@app.task(
    bind=True,
    base=RateLimitAwareTask,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 5},
    retry_backoff=True,
    retry_backoff_max=300,  # max 5 minutes between retries
)
def process_document(self, file_path: str):
    """Process a single document with Claude enrichment."""
    try:
        content = Path(file_path).read_text()
        enriched = enrich_with_claude(content)
        embed_and_store(enriched, file_path)
    except anthropic.RateLimitError as e:
        raise self.retry(exc=e, countdown=60)
```

### Chunked Batch Submission

```python
def submit_ingestion_batch(file_paths: list[str], batch_size: int = 50):
    """Submit files in batches to avoid overwhelming the queue."""
    groups = [file_paths[i:i+batch_size] for i in range(0, len(file_paths), batch_size)]

    for batch_num, batch in enumerate(groups, 1):
        print(f"Submitting batch {batch_num}/{len(groups)} ({len(batch)} files)")
        job = group(process_document.s(fp) for fp in batch)
        result = job.apply_async()
        result.save()
        time.sleep(1)  # brief pause between batches
```

### Progress Monitoring

```python
from celery.result import GroupResult

def watch_progress(group_id: str):
    """Poll and display progress for a submitted group."""
    result = GroupResult.restore(group_id)
    while not result.ready():
        completed = result.completed_count()
        total = len(result.results)
        pct = completed / total * 100
        print(f"\r  Progress: {completed}/{total} ({pct:.1f}%)", end="", flush=True)
        time.sleep(5)
    print(f"\n  Completed: {result.successful()} success, {result.failed()} failed")
```

---

## When to Use Async Pipelines

| Scenario                              | Use Async? |
|---------------------------------------|------------|
| 10 small docs, one-time ingest        | No (ingest.py is fine) |
| 100+ docs with LLM enrichment         | Yes        |
| Nightly re-ingestion cron job         | Yes        |
| Real-time single-file update          | No (sync is fine for 1 file) |
| User-triggered bulk import (CSV)      | Yes        |
| CI pipeline ingest                    | Depends on doc count |

---

## Coming Soon

Full implementation covering:
- Celery app configuration for document processing
- Redis connection and queue setup
- `process_document` worker with retry logic
- Batch submission CLI
- Progress monitoring dashboard (terminal UI)
- Failure recovery and dead letter queue
- Docker Compose setup (Redis + Celery workers)

**Prerequisites:** `pip install celery redis`, `docker-compose up -d redis`
