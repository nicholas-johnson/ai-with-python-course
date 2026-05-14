# Module 12 — Capstone Project

> Everything comes together here. Over twelve modules you have built Python foundations, an agent core, LLM integration, prompt engineering, MCP tools, RAG pipelines, structured facts, knowledge graphs, multi-agent coordination, memory systems, LangChain chains, and production hardening. The capstone project integrates these into a single working application — the Pathfinder Operations AI — a full agentic system that the bridge crew can query about any aspect of the ship, hardened for production deployment.

## Learning goals

- **Design** a complete agentic application architecture.
- **Integrate** RAG, multi-agent, MCP tools, memory, and guardrails in one system.
- **Demo** realistic operational scenarios with real data.
- **Test** with integration tests that cover happy paths and failure modes.
- **Document** extension points so future developers can add capabilities.
- **Implement structured tracing** with trace IDs and spans for every request.
- **Apply reliability patterns**: retries with backoff, timeouts, circuit breakers, fallbacks.
- **Enforce cost controls**: token budgets, model tiering, caching, batching.
- **Deploy** with environment config, secrets management, containers (Docker), and health checks.

---

## Architecture overview

The capstone application is a layered system. Each layer corresponds to a module you have already completed:

```
Crew member
    ↓
[Chat API — FastAPI + SSE streaming]           (Module 1)
    ↓
[Router Agent — classifies and delegates]      (Module 9)
    ├── [RAG Agent — searches documents]       (Module 5)
    ├── [Tool Agent — calls MCP tools]         (Modules 1, 4)
    └── [Analyst Agent — structured facts]     (Module 6)
    ↓
[Supervisor — synthesises, critiques]          (Module 9)
    ↓
[Guardrails — validates output]               (Module 3)
    ↓
[Session memory — stores conversation]         (Module 7)
    ↓
[Production hardening — tracing, reliability, cost controls]
    ↓
Response to crew member
```

The user query enters through a FastAPI endpoint. The router agent classifies the query and delegates to one or more specialist agents. The supervisor collects results, runs them through guardrails, and returns a grounded answer. The conversation is stored in session memory for continuity. Every step is traced, retries handle transient failures, and cost tracking enforces budgets.

---

## Production hardening

A prototype that works on your laptop is not production software. The Pathfinder's AI handles real crew queries during emergencies — it cannot fail silently, overspend the token budget, or lose traceability. This section covers the patterns that harden the capstone for production.

### Structured tracing

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

### Retries with exponential backoff

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

### Timeouts

Every external call should have a timeout. Without one, a hung LLM API blocks your agent indefinitely. The crew sees a spinner forever; the server thread is wasted.

```python
result = await asyncio.wait_for(llm_call(), timeout=30.0)
```

Set timeouts based on expected latency: 30s for LLM generation, 5s for tool calls, 2s for database queries. When a timeout fires, fall back to a cached response or a "please try again" message.

---

### Circuit breakers

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

### Fallbacks

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

### Cost controls

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

### Deployment essentials

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

## Key components

**Chat entrypoint** — a FastAPI app with SSE streaming (Module 1). The crew member sends a message; tokens stream back in real time. Tool calls appear as events so the user sees what the AI is doing.

**Router** — analyses the query and decides which specialist(s) to invoke (Module 9). A navigation question goes to the tool agent with sensor tools. A research question goes to the RAG agent. A complex question may fan out to multiple agents.

**RAG agent** — retrieves relevant documents from the vector store and builds a grounded prompt with citations (Module 5).

**Tool agent** — discovers and calls MCP tools (Module 4). Sensor reads, crew lookups, and log searches are all available. Tool calls are validated against schemas and gated by auth scopes.

**Analyst agent** — extracts structured facts from tool results and RAG passages (Module 6). Builds or queries a knowledge graph for relationship questions.

**Supervisor** — orchestrates the workflow, runs critique loops, and assembles the final answer (Module 9). If the first answer is low-confidence, it triggers a revision.

**Guardrails** — validates the final response against schema, content filters, and confidence thresholds (Module 3). Rejected responses trigger a fallback.

**Memory** — session memory persists the conversation; long-term memory stores crew preferences (Module 7).

**Production hardening** — trace IDs propagate through every step, retries handle transient failures, circuit breakers protect against cascading failures, and cost tracking enforces budgets.

---

## Demo scenarios

The capstone demo exercises the full system with realistic queries:

**Scenario 1 — Routine status check:**
"What is the current reactor status?" → Router sends to tool agent → MCP tool reads sensor → direct answer with source.

**Scenario 2 — Research question:**
"What do the logs say about the navigation anomaly last week?" → Router sends to RAG agent → adaptive retrieval searches logs → grounded answer with citations.

**Scenario 3 — Complex analysis:**
"Compare reactor performance before and after the ion storm and recommend maintenance actions." → Router fans out to RAG agent (retrieve logs) and tool agent (current readings) → analyst extracts structured facts → supervisor synthesises → guardrails validate → cited answer with recommendations.

**Scenario 4 — Failure handling:**
LLM API times out → circuit breaker opens → fallback to cached response → error is traced and logged.

---

## Integration testing

The capstone requires integration tests that exercise the full pipeline — not just unit tests on individual components.

**Happy path tests** — send a query, verify the response contains expected data, check that tool calls were made, and confirm citations are present.

```python
async def test_status_query():
    response = await app_client.post("/chat", json={"message": "Reactor status?"})
    assert response.status_code == 200
    data = response.json()
    assert "reactor" in data["answer"].lower()
    assert len(data["tool_calls"]) > 0
```

**Failure mode tests** — simulate LLM failures, tool errors, and empty retrieval results. Verify the system degrades gracefully — fallback responses, error messages, and no crashes.

**End-to-end flow tests** — send a multi-turn conversation and verify memory continuity. The second message should reference context from the first.

---

## Extension points

A well-designed capstone is not finished — it is extensible. Document the extension points so future developers (or future you) know where to add capabilities:

- **New tools** — add a new `@mcp.tool()` function to the MCP server. The router discovers it automatically.
- **New retrieval sources** — add a backend to the retrieval layer. Register it in the router's classification logic.
- **New agent roles** — define a new specialist agent with its own system prompt and tool access. Add it to the supervisor's delegation table.
- **New guardrails** — add a validation function to the guardrail chain. It runs in sequence with existing checks.
- **New memory backends** — implement the `SessionBackend` Protocol from Module 1. Swap in Redis, Postgres, or any other store.

---

## Field rules

- **Integration tests are not optional.** Unit tests verify components; integration tests verify the system.
- **Document extension points.** The capstone should be a starting point, not a dead end.
- **Trace everything in the demo.** Show the trace alongside the answer to demonstrate production-readiness.
- **Demo failures, not just successes.** Graceful degradation is the most impressive feature.
- **Trace every request.** A trace ID is cheap; debugging without one is expensive.
- **Retry with backoff and jitter.** Flat retries cause thundering herds.
- **Budget tokens before you spend them.** Track per-session and per-day.
- **Never hard-code secrets.** Environment variables or a secrets manager — nothing else.

---

## Demos

```bash
python module-12-capstone/demo/01_architecture_overview.py
python module-12-capstone/demo/02_demo_scenario.py
python module-12-capstone/demo/03_structured_tracing.py
python module-12-capstone/demo/04_circuit_breaker.py
python module-12-capstone/demo/05_deployment_pipeline.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-capstone-app`](exercises/01-capstone-app/) | Build the integrated Pathfinder Operations AI with structured tracing. |
| [`exercises/02-harden-and-deploy`](exercises/02-harden-and-deploy/) | Add reliability patterns, cost controls, and containerise with Docker. |
| [`exercises/03-test-and-extend`](exercises/03-test-and-extend/) | Write integration tests and document extension points. |

Run tests for this module:

```bash
pytest module-12-capstone/
```

## Slides

From repo root: `pnpm slides:12`, or `cd module-12-capstone/slides && pnpm dev`.

## Reference

- All modules 1–12 — this capstone integrates everything.
- [FastAPI](https://fastapi.tiangolo.com/)
- [OpenAI API](https://platform.openai.com/docs/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [LangChain](https://python.langchain.com/)
- [OpenTelemetry Python](https://opentelemetry-python.readthedocs.io/)
- [Circuit Breaker pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Docker — Python guide](https://docs.docker.com/language/python/)
- [Twelve-Factor App](https://12factor.net/)
