# Module 12 — Productionisation

> Everything you have built so far has run on a laptop, with you watching. The Pathfinder's agent has to run for six months of mission time, answering the crew at 0300 ship time while the API it depends on is rate-limiting, the model it prefers is unavailable, and nobody is reading the console. This module covers what you add for that: trace IDs so you can reconstruct any request after the fact, retries and circuit breakers so a flaky dependency degrades the service instead of stopping it, budgets so an agent loop cannot spend the mission's token allowance in an afternoon, and the deployment details — config, secrets, containers, health checks — that let someone else run your code.

## Learning goals

- Implement **structured tracing** with trace IDs and spans.
- Apply **reliability patterns**: retries with backoff, timeouts, circuit breakers, fallbacks.
- Enforce **cost controls**: token budgets, model tiering, caching.
- Deploy with **environment config**, secrets management, and health checks.

---

## Structured tracing

A trace ID is a single string that follows one request through every function, API call, and log line it touches. Without one, a report of "the agent gave a wrong answer this morning" leaves you grepping timestamps across several services. With one, you ask the user for the ID, search for it, and read the request back in order.

A **span** represents one unit of work within a trace: an LLM call, a vector search, a tool execution. Spans nest to form a tree that shows exactly where time was spent.

```python
import uuid
import time
import json
import logging

logger = logging.getLogger(__name__)

class TraceContext:
    def __init__(self, trace_id: str | None = None):
        self.trace_id = trace_id or uuid.uuid4().hex[:16]
        self.spans: list[dict] = []
        self._open: dict[str, dict] = {}

    def start_span(self, name: str, metadata: dict | None = None) -> str:
        span_id = uuid.uuid4().hex[:12]
        span = {
            "span_id": span_id,
            "name": name,
            "start_ms": time.time() * 1000,
            "metadata": metadata or {},
        }
        self._open[span_id] = span
        return span_id

    def end_span(self, span_id: str, metadata: dict | None = None):
        span = self._open.pop(span_id)
        span["duration_ms"] = round(time.time() * 1000 - span["start_ms"], 1)
        if metadata:
            span["metadata"].update(metadata)
        self.spans.append(span)
        logger.info(json.dumps({
            "trace_id": self.trace_id,
            "span": span["name"],
            "duration_ms": span["duration_ms"],
            **span["metadata"],
        }))
```

Usage in a request handler:

```python
@app.post("/chat")
async def chat(request: ChatRequest):
    trace = TraceContext()
    sid = trace.start_span("llm_call", {"model": MODEL})
    response = client.responses.create(
        model=MODEL, reasoning={"effort": "none"}, input=messages,
    )
    trace.end_span(sid, {"tokens": response.usage.total_tokens})
    return {"reply": response.output_text, "trace_id": trace.trace_id}
```

Log each span as JSON rather than as a formatted string. Observability platforms (Datadog, Grafana, CloudWatch) index the fields, so `trace_id` and `duration_ms` become things you can filter and aggregate on instead of text you have to parse back out.

---

## Reliability patterns

LLM calls fail in production for ordinary reasons: the API returns a 500, you hit a rate limit, a model goes down for maintenance. You cannot prevent any of that from your side, so the work is in deciding what your service does when it happens.

### Retries with exponential backoff

When an API call fails, wait before retrying — and wait longer each time. Add **jitter** (a small random amount) to each delay. Without it, every client that failed during the same outage retries on the same schedule and arrives together, a pattern known as a **thundering herd**; the jitter spreads them out.

```python
import random
import asyncio
from openai import APIError, RateLimitError

async def call_with_retry(fn, *args, max_retries: int = 3, base_delay: float = 1.0):
    for attempt in range(max_retries + 1):
        try:
            return await fn(*args)
        except (APIError, RateLimitError) as e:
            if attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, base_delay)
            logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay:.1f}s: {e}")
            await asyncio.sleep(delay)
```

The delay sequence with `base_delay=1.0` looks like: ~1s, ~2.5s, ~5s, ~9s — long enough to let transient failures clear, short enough to keep the user waiting less than 20 seconds total.

### Timeouts

Every external call needs a timeout. A stalled call with no timeout holds its connection open indefinitely, and enough of those will exhaust the connection pool that healthy requests are waiting on.

```python
import asyncio

async def llm_call_with_timeout(messages, timeout_seconds: float = 30.0):
    try:
        return await asyncio.wait_for(
            client.responses.create(
                model=MODEL, reasoning={"effort": "none"}, input=messages,
            ),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError:
        logger.error("LLM call timed out")
        return None
```

Set timeouts per call type — embedding calls are fast (5-10s), simple model calls are moderate (15-30s), agent loops with several tool calls need more room (60-120s). A timeout that is too tight cuts off responses that would have arrived; one that is too loose means you hold resources for a call that was never going to return.

### Circuit breakers

A circuit breaker stops calling a service that is already failing. Once the last N calls have failed, it stops trying for a cooldown period and returns a fallback straight away. The point is to stop one failing dependency from consuming the resources the rest of the service needs: if the LLM API is down and you keep sending requests, each one occupies a connection until it times out.

```python
import time

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, cooldown_seconds: float = 60.0):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.failures = 0
        self.state = "closed"  # closed = normal, open = blocking, half-open = testing
        self.opened_at: float = 0

    def allow_request(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            if time.time() - self.opened_at >= self.cooldown_seconds:
                self.state = "half-open"
                return True
            return False
        return True  # half-open: let one request through

    def record_success(self):
        self.failures = 0
        self.state = "closed"

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = "open"
            self.opened_at = time.time()
```

Three states: **closed** (normal — requests pass through), **open** (tripped — requests are blocked, return fallback), **half-open** (cooldown elapsed — let one request through to test if the service recovered).

### Fallbacks

When the primary model is unavailable, fall through a chain of alternatives instead of returning an error:

```python
async def chat_with_fallback(messages: list[dict], trace: TraceContext) -> str:
    chain = [
        ("gpt-6-sol", call_openai),
        ("gpt-6-sol-retry", call_openai_with_retry),
        ("gpt-6-luna", call_cheap_model),
        ("cache", lookup_cached_response),
    ]
    for name, fn in chain:
        sid = trace.start_span("fallback_attempt", {"step": name})
        try:
            result = await fn(messages)
            trace.end_span(sid, {"status": "ok"})
            return result
        except Exception as e:
            trace.end_span(sid, {"status": "error", "error": str(e)})
            continue

    return "I'm temporarily unable to process requests. Please try again shortly."
```

The chain runs: primary model → the same model with backoff → a cheaper model → a cached response → a plain apology. Each rung is a worse answer than the one above it, and all of them are better than an error page.

---

## Cost controls

An agent that loops has no natural stopping point, so the cost of a bug is measured in tokens rather than in a crash you would notice. Track usage as you go and check it before each call, not at the end of the day.

Budget in **tokens** — that is the number the API reports back on every response — and convert to USD for reporting:

```python
class CostTracker:
    # USD per 1K tokens, standard tier (October 2026)
    COST_PER_1K = {
        "gpt-6-astra": {"input": 0.01, "output": 0.05},
        "gpt-6-sol": {"input": 0.002, "output": 0.01},
        "gpt-6-luna": {"input": 0.0001, "output": 0.0005},
    }

    def __init__(self, session_budget: int = 5_000, daily_budget: int = 100_000):
        self.session_budget = session_budget
        self.daily_budget = daily_budget
        self.session_tokens = 0
        self.daily_tokens = 0
        self.session_cost_usd = 0.0

    def record(self, model: str, input_tokens: int, output_tokens: int) -> float:
        rates = self.COST_PER_1K.get(model, self.COST_PER_1K["gpt-6-sol"])
        cost = (input_tokens / 1000 * rates["input"]
                + output_tokens / 1000 * rates["output"])
        self.session_tokens += input_tokens + output_tokens
        self.daily_tokens += input_tokens + output_tokens
        self.session_cost_usd += cost
        return cost

    def within_budget(self) -> bool:
        return (self.session_tokens < self.session_budget
                and self.daily_tokens < self.daily_budget)
```

**Model tiering** — route simple tasks (classification, extraction) to cheap models (`gpt-6-luna`) and reserve expensive models (`gpt-6-sol`) for complex reasoning. Reasoning effort is a second lever: the same model at `reasoning={"effort": "none"}` is far cheaper than at `"high"`, because reasoning tokens are billed as output. A routing layer that checks query complexity before choosing a model is usually the largest single saving available.

**Caching** — identical prompts produce identical responses. Hash the prompt and cache the result. For RAG pipelines, cache at the retrieval layer too — vector search results for the same query do not change between one request and the next.

**Batching** — if you have ten embeddings to create, send one API call with ten texts rather than ten calls with one each. That reduces round trips, and for embeddings it usually reduces cost as well.

---

## Deployment

### Environment config

Never hard-code configuration. Use environment variables with a `.env` file for local development and proper secrets injection in production.

```python
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
```

Use `os.environ["KEY"]` for required values and `os.getenv("KEY", default)` for optional ones. The difference matters: `os.environ` raises `KeyError` at import time, so a missing API key stops the container from starting rather than surfacing as a failed request an hour later.

### Secrets management

Environment variables are fine for local development; in production use a secrets manager (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault) so that keys can be rotated without a redeploy. Either way, secrets should not appear in code, in committed config files, or in container images.

```
# .env (local only — NEVER commit this file)
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:pass@localhost:5432/app
```

Add `.env` to `.gitignore`. In CI/CD, inject secrets via pipeline variables or a secrets manager integration.

### Docker

A minimal Dockerfile for a FastAPI + AI backend:

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Pin your base image and dependency versions. `python:3.12-slim` is small, `--no-cache-dir` keeps the image lean. Pass secrets via environment variables at runtime (`docker run -e OPENAI_API_KEY=...`), never bake them into the image.

### Health checks

A health endpoint is how the infrastructure around your service finds out whether it is working: load balancers use it to decide where to send traffic, and orchestrators use it to decide when to restart a container.

```python
@app.get("/health")
async def health():
    checks = {
        "api": "ok",
        "vector_store": await check_vector_store(),
        "llm": await check_llm_reachable(),
    }
    healthy = all(v == "ok" for v in checks.values())
    return JSONResponse(
        content={"status": "healthy" if healthy else "degraded", "checks": checks},
        status_code=200 if healthy else 503,
    )
```

Check each dependency you rely on — database, vector store, LLM API reachability — and return 200 when they all pass, 503 when any of them does not. Return the individual results too, so the response says which dependency is down rather than only that something is.

---

## Summary

- **Trace every request.** A trace ID costs nothing, and it is how you reconstruct one request afterwards.
- **Retry with backoff, then fall back.** Jitter stops a thundering herd. A cheaper model or a cached answer is still an answer.
- **Budget tokens before you spend them.** Track per-session and per-day. Check the cap before the call, not after the bill.
- **Config and secrets stay out of the code.** Environment variables locally, a secrets manager in production, and a health check on the container.

---

## Demos

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python module-12-productionisation/demo/demo.py

# Option B - uv (no activation needed):
uv run python module-12-productionisation/demo/demo.py
```

Menu, `a` runs all three. Parts 1 and 3 make live API calls; part 2 is offline.

1. **Structured tracing** — spans through a classify → answer → guardrail pipeline, printed as JSON (needs a key)
2. **Circuit breaker** — a failing ship service takes the breaker closed → open → half-open → closed (no key)
3. **Cost controls** — token budget, complexity routing between `gpt-6-luna` and `gpt-6-sol`, running spend (needs a key)

## Exercises

The three exercises are independent; each one hardens a different part of the same request path.

| Folder | What you build |
| ------ | -------------- |
| [`exercises/01-tracing`](exercises/01-tracing/) | `TraceContext` with nested spans, durations, and one JSON log line per span |
| [`exercises/02-reliability`](exercises/02-reliability/) | Retry with backoff and jitter, a circuit breaker, and a fallback chain |
| [`exercises/03-cost-controls`](exercises/03-cost-controls/) | Token budgets, a model-tiering router, and a prompt cache |

All three run with no API key — the tests drive a scripted client.

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pytest module-12-productionisation/ -v

# Option B - uv (no activation needed):
uv run --extra dev pytest module-12-productionisation/ -v
```

## Capstones

The four full-stack capstone apps (Recipe Finder, Movie Night, Travel Planner, Personal Assistant) live in [`extras/`](../extras/). They combine this module's patterns with techniques from **Module 13 — Edge Topics**, so do them after Module 13.

## Slides

From repo root: `pnpm slides:12`, or `cd module-12-productionisation/slides && pnpm dev`.

## Reference

- [OpenTelemetry — traces and spans](https://opentelemetry.io/docs/concepts/signals/traces/) — the vendor-neutral model `TraceContext` is a miniature of
- [Google SRE Book — Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/) — thundering herds, retry budgets, graceful degradation
- [Martin Fowler — CircuitBreaker](https://martinfowler.com/bliki/CircuitBreaker.html) — the three-state pattern in its original form
- [Michael Nygard — *Release It!*](https://pragprog.com/titles/mnee2/release-it-second-edition/) — where circuit breakers and bulkheads were introduced
- [AWS — Exponential backoff and jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) — why jitter matters, with the maths
- [OpenAI — Rate limits](https://platform.openai.com/docs/guides/rate-limits) — the errors your retry logic is catching
- [The Twelve-Factor App — Config](https://12factor.net/config) — the environment-variable convention this module follows
