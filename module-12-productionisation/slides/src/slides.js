export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 12 — Productionisation',
      subtitle: 'From prototype to production-ready AI',
      icon: 'shield',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'From prototype to production',
      points: [
        'Your prototype works on your laptop. That is not the same as production software.',
        'Production AI systems must be **traceable**, **reliable**, **cost-aware**, and **deployable**.',
        'This module teaches the patterns. Then you pick a capstone app and build it for real.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Implement **structured tracing** with trace IDs and spans for every request.',
        'Apply **reliability patterns**: retries with backoff, timeouts, circuit breakers, fallbacks.',
        'Enforce **cost controls**: token budgets, model tiering, caching.',
        'Deploy with **environment config**, secrets management, containers, and health checks.',
      ],
    },
  },

  // --- Structured tracing ---

  {
    type: 'title',
    content: {
      title: 'Structured tracing',
      subtitle: 'Know exactly what happened on every request',
      icon: 'search',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Why tracing matters',
      icon: 'search',
      points: [
        'User reports: "the AI gave a wrong answer at 14:32." Which request? What did the model see?',
        'Every request gets a **trace ID** — a unique identifier that propagates through every step.',
        'Each step is a **span** with timing, status, and metadata.',
        'Log spans as JSON. In production, send to **Datadog**, **Jaeger**, or **OpenTelemetry**.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'TraceContext',
      code: `class TraceContext:
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

    def end_span(self, span, status="ok", metadata=None):
        span["end_time"] = time.time()
        span["duration_ms"] = (span["end_time"] - span["start_time"]) * 1000
        span["status"] = status
        if metadata:
            span["metadata"] = metadata`,
      highlights: [
        'Every request gets a **trace_id** — propagate it through every function.',
        'Each span captures **timing** and **status** — find the slow step instantly.',
        'Log as **JSON** — structured logs are searchable, unstructured logs are not.',
      ],
    },
  },

  // --- Demo: tracing ---

  {
    type: 'title',
    content: {
      title: 'Demo — Structured tracing',
      subtitle: 'Trace IDs propagating through a request pipeline',
      icon: 'cpu',
    },
  },

  // --- Reliability patterns ---

  {
    type: 'title',
    content: {
      title: 'Reliability patterns',
      subtitle: 'Expect failure. Handle it gracefully.',
      icon: 'shield',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'What can go wrong',
      icon: 'shield',
      points: [
        '**Network blips** — transient connection failures to LLM APIs.',
        '**Rate limits** — API returns 429 when you hit the quota.',
        '**Timeouts** — model takes too long, your server thread is blocked.',
        '**Cascading failures** — one failing service brings down the whole system.',
        'The answer: **retries**, **timeouts**, **circuit breakers**, **fallbacks**.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Retries with exponential backoff',
      code: `async def retry_with_backoff(fn, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            return await fn()
        except TransientError:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
            await asyncio.sleep(delay)`,
      highlights: [
        '**Exponential backoff**: 1s → 2s → 4s — gives the service time to recover.',
        '**Jitter** (random.uniform) prevents thundering herd when many clients retry simultaneously.',
        'Only retry on **transient errors** (5xx, timeout, rate limit) — never on 4xx.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Circuit breaker',
      code: `class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_time=60):
        self.failures = 0
        self.threshold = failure_threshold
        self.recovery_time = recovery_time
        self.state = "closed"  # closed = normal, open = failing

    async def call(self, fn):
        if self.state == "open":
            if time.time() - self.last_failure > self.recovery_time:
                self.state = "half-open"  # allow one test request
            else:
                raise CircuitOpenError("Service unavailable")
        try:
            result = await fn()
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
        '**Closed** = normal operation. **Open** = failing fast, no requests sent.',
        'After recovery_time, enters **half-open** — one test request decides.',
        'Prevents wasting resources hammering a broken service.',
      ],
    },
  },
  {
    type: 'comparison',
    content: {
      title: 'Without vs with reliability patterns',
      left: {
        label: 'No protection',
        items: [
          'API timeout → server thread blocked forever',
          'Rate limit → retry immediately → get rate limited again',
          'Service down → every request fails slowly',
          'Users see errors and spinners',
        ],
      },
      right: {
        label: 'With patterns',
        items: [
          'Timeout fires → fallback response in 2 seconds',
          'Backoff + jitter → automatic recovery',
          'Circuit breaker → fail fast, try fallback model',
          'Users get answers (maybe degraded) instead of errors',
        ],
      },
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Fallback chains',
      icon: 'refresh-cw',
      points: [
        'When the primary model fails, fall back — do not just return an error.',
        'Fallback chain: **primary model** → **cheaper model** → **cached response** → **graceful error**.',
        'The user experience degrades gradually, never crashes.',
        '`asyncio.wait_for(call, timeout=30)` — every external call gets a timeout.',
      ],
    },
  },

  // --- Demo: circuit breaker ---

  {
    type: 'title',
    content: {
      title: 'Demo — Circuit breaker',
      subtitle: 'Watch the breaker open, fail fast, and recover',
      icon: 'cpu',
    },
  },

  // --- Cost controls ---

  {
    type: 'title',
    content: {
      title: 'Cost controls',
      subtitle: 'LLM tokens cost money. Budget before you spend.',
      icon: 'list',
    },
  },
  {
    type: 'code',
    content: {
      title: 'Token budget tracking',
      code: `class CostTracker:
    def __init__(self, session_budget=10_000, daily_budget=1_000_000):
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
                and self.daily_usage < self.daily_budget)`,
      highlights: [
        'Track usage **per session** and **per day**. Reject requests over budget.',
        '**Model tiering** is the biggest lever: classification → cheap model, reasoning → expensive.',
        '**Caching** similar queries avoids redundant LLM calls entirely.',
      ],
    },
  },

  // --- Demo: cost controls ---

  {
    type: 'title',
    content: {
      title: 'Demo — Cost controls',
      subtitle: 'Token budgets, model tiering, and cost tracking',
      icon: 'cpu',
    },
  },

  // --- Deployment ---

  {
    type: 'title',
    content: {
      title: 'Deployment',
      subtitle: 'Config, secrets, containers, health checks',
      icon: 'server',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Deployment essentials',
      icon: 'server',
      points: [
        '**Environment config** — `python-dotenv` for dev, real env vars in production. Never hard-code.',
        '**Secrets** — API keys in `.env` (gitignored), secrets manager in production.',
        '**Containers** — Dockerfile packages the app with its dependencies for consistent deployment.',
        '**Health checks** — `/health` endpoint returns 200 when the service is ready. Check dependencies.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Dockerfile for an AI API',
      code: `FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s \\
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/health').raise_for_status()"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]`,
      highlights: [
        '**HEALTHCHECK** — orchestrators use this to route traffic only to healthy instances.',
        '**Slim base image** — smaller attack surface, faster builds.',
        'Copy requirements first — Docker caches the layer, rebuilds only when deps change.',
      ],
    },
  },

  // --- Field rules ---

  {
    type: 'rules',
    content: {
      title: 'Production field rules',
      rules: [
        {
          rule: 'Trace every request',
          example: 'A trace ID is cheap. Debugging without one is expensive.',
          icon: 'search',
        },
        {
          rule: 'Retry with backoff and jitter',
          example: 'Flat retries cause thundering herds. Exponential backoff with jitter prevents them.',
          icon: 'refresh-cw',
        },
        {
          rule: 'Budget tokens before you spend them',
          example: 'Track per-session and per-day. A runaway agent produces a surprising bill.',
          icon: 'list',
        },
        {
          rule: 'Never hard-code secrets',
          example: 'Environment variables or a secrets manager. Nothing else.',
          icon: 'shield',
        },
        {
          rule: 'Demo failures, not just successes',
          example: 'Graceful degradation is the most impressive production feature.',
          icon: 'cpu',
        },
      ],
    },
  },

  // --- Capstone exercises ---

  {
    type: 'title',
    content: {
      title: 'Capstone exercises',
      subtitle: 'Choose one. Build it production-ready.',
      icon: 'pen-tool',
    },
  },
  {
    type: 'cards',
    content: {
      title: 'Pick your capstone',
      cards: [
        {
          heading: 'AI Recipe Finder',
          points: [
            'Photo your fridge, get recipe suggestions.',
            'RAG + hybrid search + multimodal vision.',
            'Allergen guardrails + semantic caching.',
          ],
        },
        {
          heading: 'AI Movie Night',
          points: [
            'Describe your mood, get movie picks.',
            'RAG + reranking + text-to-SQL for data questions.',
            'Charts and structured output.',
          ],
        },
        {
          heading: 'AI Travel Planner',
          points: [
            'Describe your dream trip, get a day-by-day itinerary.',
            'Agentic RAG + tool calling + web fallback.',
            'Budget tracking + structured itineraries.',
          ],
        },
        {
          heading: 'AI Personal Assistant',
          points: [
            'Friendly companion with calendar, notes, reminders.',
            'Chat + tool calling + MCP + RAG over notes.',
            'Session memory + cost controls.',
          ],
        },
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'How the capstones work',
      icon: 'pen-tool',
      points: [
        'Each exercise has a **frontend/** (SvelteKit — provided), a **starter/** (your code), and a **solution/**.',
        'You build the **FastAPI backend** in `starter/` — the frontend connects automatically.',
        'Apply the production patterns from this module: **tracing**, **retries**, **cost tracking**.',
        'Run with `uvicorn app:app --reload --port 8000` and `cd frontend && pnpm dev`.',
      ],
    },
  },
];
