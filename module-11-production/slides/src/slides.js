export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 11 — Production & Deployment',
      subtitle: 'Observability, resilience, cost, and shipping aboard the Pathfinder',
      icon: 'sliders',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Launch is not the finish line',
      points: [
        'Agentic systems must be observable, resilient, and affordable.',
        'Tracing, reliability patterns, cost controls, and deployment.',
        'If you cannot debug it in production, you cannot run it in production.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Add **tracing and structured logging** so every call is debuggable.',
        'Implement **reliability**: retries, timeouts, circuit breakers, fallbacks.',
        'Apply **cost controls**: caching, batching, model selection, token budgets.',
        'Ship with confidence: **environment config**, secrets, containers, CI/CD.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Structured tracing',
      icon: 'activity',
      points: [
        'Every request gets a **trace ID** that propagates through all calls.',
        'Each tool call is a **span**: start time, duration, outcome, tool name.',
        'Structured JSON logs with trace_id, span_id, and timing.',
        'Correlate logs across services: "This answer took 3s because tool X timed out."',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Trace middleware',
      code: `import uuid, time, json

def traced_tool_call(tool_name, args, trace_id=None):
    trace_id = trace_id or str(uuid.uuid4())
    span_id = str(uuid.uuid4())[:8]
    start = time.time()

    try:
        result = tools[tool_name](**args)
        status = "ok"
    except Exception as e:
        result, status = str(e), "error"

    log_entry = {
        "trace_id": trace_id, "span_id": span_id,
        "tool": tool_name, "status": status,
        "duration_ms": round((time.time() - start) * 1000),
        "preview": str(result)[:200],
    }
    logger.info(json.dumps(log_entry))
    return result`,
      highlights: [
        'trace_id links all calls in one user request',
        'Preview is truncated — never log full payloads or secrets',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Reliability patterns',
      icon: 'shield',
      points: [
        '**Retry with backoff**: transient failures often resolve on retry.',
        '**Timeout**: do not wait forever for a slow model or tool.',
        '**Circuit breaker**: stop calling a broken service, fail fast.',
        '**Fallback**: if the primary model fails, fall back to a cheaper one.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Retry with exponential backoff',
      code: `import time

def retry_with_backoff(fn, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except TransientError:
            if attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)`,
      highlights: [
        'Exponential backoff: 1s, 2s, 4s — gives the service time to recover',
        'Only retry transient errors — permanent failures should fail immediately',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Circuit breaker',
      code: `class CircuitBreaker:
    def __init__(self, threshold=5, reset_timeout=60):
        self.threshold = threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure = 0
        self.state = "closed"  # closed | open | half-open

    def call(self, fn):
        if self.state == "open":
            if time.time() - self.last_failure > self.reset_timeout:
                self.state = "half-open"
            else:
                raise CircuitOpenError("Service unavailable")

        try:
            result = fn()
            self.failures = 0
            self.state = "closed"
            return result
        except Exception:
            self.failures += 1
            self.last_failure = time.time()
            if self.failures >= self.threshold:
                self.state = "open"
            raise`,
      highlights: [
        'Closed = normal. Open = reject immediately. Half-open = try one.',
        'Protects downstream services from cascading failure',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Cost controls',
      icon: 'dollar-sign',
      points: [
        '**Token budgets**: cap per-session and per-request token spend.',
        '**Model tiering**: cheap model for easy queries, expensive for hard ones.',
        '**Caching**: identical queries return cached responses (exact or semantic).',
        '**Batching**: group independent requests to reduce API call overhead.',
        '**Monitoring**: track spend per user, session, and model — alert on anomalies.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Cost tracker',
      code: `class CostTracker:
    def __init__(self, session_budget: float):
        self.session_budget = session_budget
        self.total_cost = 0.0
        self.calls: list[dict] = []

    def record(self, model, input_tokens, output_tokens):
        cost = self._calculate_cost(model, input_tokens, output_tokens)
        self.total_cost += cost
        self.calls.append({"model": model, "cost": cost})

        if self.total_cost > self.session_budget:
            raise BudgetExceededError(
                f"Session cost {self.total_cost:.4f} "
                f"exceeds budget {self.session_budget:.4f}")
        return cost`,
      highlights: [
        'Per-session budgets prevent runaway costs from long conversations',
        'Cost data feeds dashboards and alerting systems',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Deployment essentials',
      icon: 'package',
      points: [
        '**Environment config**: dev / staging / prod settings via env vars.',
        '**Secrets management**: API keys in env vars or vaults, never in code.',
        '**Containers**: Dockerfile for reproducible builds.',
        '**Health checks**: `/health` endpoint for load balancers and orchestrators.',
        '**CI/CD**: automated tests → build → deploy on every merge.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Dockerfile for the agent',
      code: `FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s \\
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]`,
      highlights: [
        'Install dependencies first for Docker layer caching',
        'HEALTHCHECK lets orchestrators know when the service is ready',
      ],
    },
  },
  {
    type: 'rules',
    content: {
      title: 'Field rules — Module 11',
      rules: [
        {
          rule: 'Trace everything',
          example: 'If you cannot find it in the logs, it did not happen.',
          icon: 'activity',
        },
        {
          rule: 'Budget before you call',
          example: 'Check the cost tracker before sending tokens to the model.',
          icon: 'dollar-sign',
        },
        {
          rule: 'Fail fast, fall back gracefully',
          example: 'Circuit breaker + fallback model = resilient pipeline.',
          icon: 'shield',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises — Shipping the Pathfinder',
      points: [
        '01 — Trace middleware: add trace IDs and timing to every tool call',
        '02 — Batch pipeline: batch LLM requests with retry and fallback',
        '03 — Cost tracker: per-session token and cost budget enforcement',
        '04 — Deploy container: health-check app, env config, Dockerfile validation',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Production ready — Module 11',
      subtitle: 'Observable, resilient, affordable. Next: LangChain.',
      icon: 'party-popper',
    },
  },
];
