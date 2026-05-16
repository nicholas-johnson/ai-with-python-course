# Module 12 — Productionisation

Your prototype works on your laptop — now make it production-ready. This module teaches the patterns that turn AI prototypes into reliable, cost-effective, traceable production systems. Then pick one of four capstone apps and build it.

## Learning goals

- Implement **structured tracing** with trace IDs and spans.
- Apply **reliability patterns**: retries with backoff, timeouts, circuit breakers, fallbacks.
- Enforce **cost controls**: token budgets, model tiering, caching.
- Deploy with **environment config**, secrets management, and health checks.

---

## Structured tracing

Every production request needs a trace ID — a single string that follows the request through every function, API call, and log line. When something breaks at 3 AM, a trace ID is the difference between five minutes of debugging and five hours.

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
    sid = trace.start_span("llm_call", {"model": "gpt-4o-mini"})
    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=messages,
    )
    trace.end_span(sid, {"tokens": response.usage.total_tokens})
    return {"reply": response.choices[0].message.content, "trace_id": trace.trace_id}
```

Every log line is structured JSON — no `print()`, no f-string logs. Structured logs feed directly into observability platforms (Datadog, Grafana, CloudWatch). When a user reports a problem, you search by `trace_id` and see every span in order.

---

## Reliability patterns

Production LLM calls fail. APIs return 500s, rate limits kick in, models go down for maintenance. Reliability is not about preventing failures — it is about surviving them.

### Retries with exponential backoff

When an API call fails, wait before retrying — and wait longer each time. Add **jitter** (randomness) so that a thousand clients that all fail at once do not all retry at the same instant, causing a **thundering herd** that takes the API down again.

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

Every external call needs a timeout. Without one, a stalled API call holds a connection open forever, leaking resources until the server falls over.

```python
import asyncio

async def llm_call_with_timeout(messages, timeout_seconds: float = 30.0):
    try:
        return await asyncio.wait_for(
            client.chat.completions.create(
                model="gpt-4o-mini", messages=messages,
            ),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError:
        logger.error("LLM call timed out")
        return None
```

Set timeouts per call type — embedding calls are fast (5-10s), simple completions are moderate (15-30s), complex agent loops with tool calls need more room (60-120s). Too tight and you clip valid responses; too loose and you waste resources waiting.

### Circuit breakers

A circuit breaker stops calling a failing service. If the last N calls all failed, stop trying for a cooldown period and return a fallback immediately. This prevents cascading failures — when the LLM API is down, you do not want every request queuing up and exhausting your connection pool.

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
        ("gpt-4o-mini", call_openai),
        ("gpt-4o-mini", call_openai_with_retry),
        ("gpt-3.5-turbo", call_cheap_model),
        ("cache", lookup_cached_response),
    ]
    for name, fn in chain:
        sid = trace.start_span("fallback_attempt", {"provider": name})
        try:
            result = await fn(messages)
            trace.end_span(sid, {"status": "ok"})
            return result
        except Exception as e:
            trace.end_span(sid, {"status": "error", "error": str(e)})
            continue

    return "I'm temporarily unable to process requests. Please try again shortly."
```

The fallback chain: primary model → retry with backoff → cheaper model → cached response → graceful error message. The user gets a degraded but working response instead of a stack trace.

---

## Cost controls

LLM calls cost money. A single runaway loop can burn through a daily budget in minutes. Track spend in real time and enforce hard limits.

```python
class CostTracker:
    COST_PER_1K = {
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    }

    def __init__(self, session_budget: float = 1.0, daily_budget: float = 50.0):
        self.session_budget = session_budget
        self.daily_budget = daily_budget
        self.session_spent = 0.0
        self.daily_spent = 0.0

    def record(self, model: str, input_tokens: int, output_tokens: int) -> float:
        rates = self.COST_PER_1K.get(model, {"input": 0.01, "output": 0.03})
        cost = (input_tokens / 1000 * rates["input"]
                + output_tokens / 1000 * rates["output"])
        self.session_spent += cost
        self.daily_spent += cost
        return cost

    def check_budget(self) -> bool:
        return (self.session_spent < self.session_budget
                and self.daily_spent < self.daily_budget)
```

**Model tiering** — route simple tasks (classification, extraction) to cheap models (`gpt-4o-mini`) and reserve expensive models (`gpt-4o`) for complex reasoning. A routing layer that checks query complexity before choosing a model can cut costs by 60-80%.

**Caching** — identical prompts produce identical responses. Hash the prompt and cache the result. For RAG pipelines, cache at the retrieval layer too — vector search results for the same query do not change every second.

**Batching** — if you have ten embeddings to create, send one API call with ten texts, not ten API calls with one text each. Batching reduces overhead and often reduces cost.

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

Use `os.environ["KEY"]` (raises `KeyError` if missing) for required values and `os.getenv("KEY", default)` for optional ones. Fail loud and early — a missing API key at startup is better than a crash mid-request.

### Secrets management

Environment variables work for local development, but in production use a secrets manager (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault). The key principle: secrets never appear in code, config files, or container images.

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

Every production service needs a health endpoint. Load balancers use it to route traffic, orchestrators use it to restart crashed containers.

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

Check every dependency: database, vector store, LLM API reachability. Return 200 when healthy, 503 when degraded. Include individual check results so you can see exactly what is down.

---

## Field rules

- **Trace every request.** A trace ID is cheap; debugging without one is expensive.
- **Retry with backoff and jitter.** Flat retries cause thundering herds.
- **Budget tokens before you spend them.** Track per-session and per-day.
- **Never hard-code secrets.** Environment variables or a secrets manager.
- **Integration tests are not optional.**
- **Demo failures, not just successes.** Graceful degradation is impressive.

---

## Exercises

| # | App | Directory | Key techniques |
|---|-----|-----------|----------------|
| 01 | AI Recipe Finder | [`exercises/01-recipe-finder/`](exercises/01-recipe-finder/) | RAG, hybrid search, reranking, multimodal vision, allergen guardrails |
| 02 | AI Movie Night | [`exercises/02-movie-night/`](exercises/02-movie-night/) | RAG, hybrid search, text-to-SQL, structured output |
| 03 | AI Travel Planner | [`exercises/03-travel-planner/`](exercises/03-travel-planner/) | Agentic RAG, tool calling, structured itineraries, web fallback |
| 04 | AI Personal Assistant | [`exercises/04-personal-assistant/`](exercises/04-personal-assistant/) | Chat + tools + MCP, RAG notes, calendar, cost controls |

Choose one exercise. Each provides a SvelteKit frontend — you build the FastAPI backend.

---

## Running

### Tests

```bash
pytest module-12-productionisation/
```

### Slides

From repo root: `pnpm slides:12`, or `cd module-12-productionisation/slides && pnpm dev`.
