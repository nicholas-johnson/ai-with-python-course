# Module 11 — Production & Deployment

> A prototype that works on your laptop is not production software. The Pathfinder's AI handles real crew queries during emergencies — it cannot fail silently, overspend the token budget, or lose traceability. This module hardens the agent for production: structured tracing so you can debug any request, reliability patterns that survive transient failures, cost controls that prevent surprise bills, and deployment practices from environment config to containers.

## Learning goals

- Implement **structured tracing** with trace IDs and spans.
- Apply **reliability patterns**: retries with backoff, timeouts, circuit breakers, fallbacks.
- Enforce **cost controls**: token budgets, model tiering, caching, batching.
- Deploy with **environment config**, **secrets management**, **containers** (Docker), and **health checks**.

---

## Structured tracing

When a crew member reports "the AI gave a wrong answer at 14:32," you need to find that exact request, see what the model received, what tools were called, and what was returned. Structured tracing makes this possible.

Every request gets a **trace ID** — a unique identifier that propagates through every step. Each step within the request is a **span** with timing, status, and metadata.

```python
import uuid
import time

class TraceContext:
    def __init__(self):
        self.trace_id = str(uuid.uuid4())
        self.spans: list[dict] = []

    def start_span(self, name: str) -> dict:
        span = {
            "span_id": str(uuid.uuid4()),
            "trace_id": self.trace_id,
            "name": name,
            "start_time": time.time(),
        }
        self.spans.append(span)
        return span

    def end_span(self, span: dict, status: str = "ok", metadata: dict = None):
        span["end_time"] = time.time()
        span["duration_ms"] = (span["end_time"] - span["start_time"]) * 1000
        span["status"] = status
        if metadata:
            span["metadata"] = metadata
```

Log spans as JSON. Each entry includes timing (how long the LLM call took), outcome (success/error), and a safe preview of the result (no secrets, no full payloads). In production, send these to an observability platform (Datadog, Jaeger, or OpenTelemetry).

---

## Retries with exponential backoff

LLM APIs are not 100% reliable. Network blips, rate limits, and transient server errors happen. Retries handle these automatically — but only if you back off exponentially to avoid hammering a struggling service.

```python
import random

async def retry_with_backoff(fn, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            return await fn()
        except TransientError:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
            await asyncio.sleep(delay)
```

**Jitter** (`random.uniform`) prevents thundering-herd problems when many clients retry simultaneously. Only retry on transient errors (5xx, timeout, rate limit) — retrying on 4xx (bad request) just wastes quota.

---

## Timeouts

Every external call should have a timeout. Without one, a hung LLM API blocks your agent indefinitely. The crew sees a spinner forever; the server thread is wasted.

```python
result = await asyncio.wait_for(llm_call(), timeout=30.0)
```

Set timeouts based on expected latency: 30s for LLM generation, 5s for tool calls, 2s for database queries. When a timeout fires, fall back to a cached response or a "please try again" message.

---

## Circuit breakers

If a service is consistently failing, retrying every request wastes resources and adds latency. A **circuit breaker** tracks failure rates and "opens" the circuit when failures exceed a threshold — subsequent calls fail immediately without attempting the request.

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_time=60):
        self.failures = 0
        self.threshold = failure_threshold
        self.recovery_time = recovery_time
        self.last_failure_time = 0
        self.state = "closed"  # closed = normal, open = failing

    async def call(self, fn):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_time:
                self.state = "half-open"
            else:
                raise CircuitOpenError("Service unavailable")

        try:
            result = await fn()
            self.failures = 0
            self.state = "closed"
            return result
        except Exception:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.threshold:
                self.state = "open"
            raise
```

After the recovery period, the breaker enters "half-open" state and allows one test request. If it succeeds, the circuit closes. If it fails, the circuit opens again.

---

## Fallbacks

When the primary model fails (or the circuit is open), fall back to a cheaper or cached alternative rather than returning an error.

```python
async def resilient_complete(prompt: str) -> str:
    try:
        return await primary_model.complete(prompt)
    except (TimeoutError, CircuitOpenError):
        return await fallback_model.complete(prompt)
    except Exception:
        return "I'm unable to process this request right now. Please try again."
```

The fallback chain: primary model → cheaper model → cached response → graceful error message.

---

## Cost controls

LLM tokens cost money. Without budgets, a runaway agent or a high-traffic day can produce a surprising bill.

**Token budgets** — track usage per session and per day. Reject requests that would exceed the budget.

```python
class CostTracker:
    def __init__(self, session_budget: int = 10000, daily_budget: int = 1000000):
        self.session_usage = 0
        self.daily_usage = 0
        self.session_budget = session_budget
        self.daily_budget = daily_budget

    def record(self, prompt_tokens: int, completion_tokens: int):
        total = prompt_tokens + completion_tokens
        self.session_usage += total
        self.daily_usage += total

    def within_budget(self) -> bool:
        return (self.session_usage < self.session_budget
                and self.daily_usage < self.daily_budget)
```

**Model tiering** — route simple queries to cheap models, complex queries to expensive ones. Classification → GPT-4o-mini. Reasoning → GPT-4o. This is the biggest cost lever.

**Caching** — if the same query was answered recently, return the cached response. Exact-match caching is simple; semantic caching (matching similar queries) is more powerful but requires embedding comparisons.

**Batching** — group multiple small requests into one API call when the model supports it. Reduces per-request overhead.

---

## Deployment essentials

**Environment config** — load settings from environment variables, not hard-coded values. Use `python-dotenv` for local development, real environment variables in production.

```python
import os
from dotenv import load_dotenv

load_dotenv()

config = {
    "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    "api_key": os.getenv("OPENAI_API_KEY"),
    "max_tokens": int(os.getenv("MAX_TOKENS", "4096")),
}
```

**Secrets management** — API keys never go in code or version control. Use environment variables, a secrets manager (AWS Secrets Manager, HashiCorp Vault), or a `.env` file that is in `.gitignore`.

**Containers** — a Dockerfile packages the application with its dependencies for consistent deployment anywhere.

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY . .
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Health checks** — the `/health` endpoint returns 200 when the service is ready. Orchestrators (Docker, Kubernetes) use this to decide whether to route traffic to the instance. Check dependencies (database connection, API reachability) in the health endpoint.

---

## Field rules

- **Trace every request.** A trace ID is cheap; debugging without one is expensive.
- **Retry with backoff and jitter.** Flat retries cause thundering herds.
- **Budget tokens before you spend them.** Track per-session and per-day.
- **Never hard-code secrets.** Environment variables or a secrets manager — nothing else.

---

## Demos

```bash
python module-11-production/demo/01_structured_tracing.py
python module-11-production/demo/02_circuit_breaker.py
python module-11-production/demo/03_deployment_pipeline.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-trace-middleware`](exercises/01-trace-middleware/) | Propagate trace IDs with per-tool timing and structured logs. |
| [`exercises/02-batch-pipeline`](exercises/02-batch-pipeline/) | Batch completions with retries on transient errors and fallbacks. |
| [`exercises/03-cost-tracker`](exercises/03-cost-tracker/) | Track per-call usage and enforce session budgets. |
| [`exercises/04-deploy-container`](exercises/04-deploy-container/) | Build a health-check app, load env config, validate a Dockerfile. |

Run tests for this module:

```bash
pytest module-11-production/
```

## Slides

From repo root: `pnpm slides:11`, or `cd module-11-production/slides && pnpm dev`.

## Reference

- [OpenTelemetry Python](https://opentelemetry-python.readthedocs.io/)
- [Circuit Breaker pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Docker — Python guide](https://docs.docker.com/language/python/)
- [Twelve-Factor App](https://12factor.net/)
