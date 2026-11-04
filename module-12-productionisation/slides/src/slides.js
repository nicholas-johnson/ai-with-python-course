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
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Implement **structured tracing** with trace IDs and spans for every request.',
        'Apply **reliability patterns**: retries with backoff, timeouts, circuit breakers, fallbacks.',
        'Enforce **cost controls**: token budgets, model tiering, caching.',
        'Deploy with **environment config**, secrets, containers, and health checks — including a **Google Cloud** path.',
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
        'A crew member reports a wrong answer this morning. Which request was it, and what did the model see?',
        'Every request gets a **trace ID** — one identifier carried through every step it touches.',
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

  // {
  //   type: 'title',
  //   content: {
  //     title: 'Demo — Structured tracing',
  //     subtitle: 'Trace IDs propagating through a request pipeline',
  //     icon: 'cpu',
  //   },
  // },

  // --- Reliability patterns ---

  {
    type: 'title',
    content: {
      title: 'Reliability patterns',
      subtitle: 'Dependencies fail. Decide what happens next.',
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
        '**Timeouts** — the model takes too long and your server thread is still waiting.',
        '**Cascading failures** — one slow dependency ties up the resources every other request needs.',
        'Four answers: **retries**, **timeouts**, **circuit breakers**, **fallbacks**.',
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
        '**Jitter** (random.uniform) spreads out clients that all failed at the same moment.',
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
        '**Closed** = normal operation. **Open** = requests rejected locally, none sent.',
        'After recovery_time, enters **half-open** — one test request decides.',
        'A dead dependency stops occupying connections that healthy requests need.',
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
          'No timeout → the thread waits on a call that never returns',
          'Rate limit → immediate retry → rate limited again',
          'Service down → every request waits its full timeout',
          'The crew sees errors and spinners',
        ],
      },
      right: {
        label: 'With patterns',
        items: [
          'Timeout fires → fallback response in 2 seconds',
          'Backoff + jitter → recovers without a coordinated retry spike',
          'Circuit breaker → reject locally, try the fallback model',
          'The crew gets an answer, sometimes a degraded one',
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
        'When the primary model fails, fall through the chain rather than returning an error.',
        'Fallback chain: **primary model** → **cheaper model** → **cached response** → **plain apology**.',
        'Each rung is a worse answer than the one above it, and all of them beat a 500.',
        '`asyncio.wait_for(call, timeout=30)` — every external call gets a timeout.',
      ],
    },
  },

  // --- Demo: circuit breaker ---

  // {
  //   type: 'title',
  //   content: {
  //     title: 'Demo — Circuit breaker',
  //     subtitle: 'Watch the breaker open, fail fast, and recover',
  //     icon: 'cpu',
  //   },
  // },

  // --- Cost controls ---

  {
    type: 'title',
    content: {
      title: 'Cost controls',
      subtitle: 'An agent loop has no natural stopping point',
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

  // {
  //   type: 'title',
  //   content: {
  //     title: 'Demo — Cost controls',
  //     subtitle: 'Token budgets, model tiering, and cost tracking',
  //     icon: 'cpu',
  //   },
  // },

  // --- Deployment ---

  //   {
  //     type: 'title',
  //     content: {
  //       title: 'Deployment',
  //       subtitle: 'Config, secrets, containers, health checks',
  //       icon: 'server',
  //     },
  //   },
  //   {
  //     type: 'standard',
  //     content: {
  //       title: 'Deployment essentials',
  //       icon: 'server',
  //       points: [
  //         '**Environment config** — `python-dotenv` for dev, real env vars in production. Never hard-code.',
  //         '**Secrets** — API keys in `.env` (gitignored), secrets manager in production.',
  //         '**Containers** — Dockerfile packages the app with its dependencies for consistent deployment.',
  //         '**Health checks** — `/health` endpoint returns 200 when the service is ready. Check dependencies.',
  //         'Provider-specific mappings: **AWS / Azure / GCP** sections below.',
  //       ],
  //     },
  //   },
  //   {
  //     type: 'code',
  //     content: {
  //       title: 'Dockerfile for an AI API',
  //       code: `FROM python:3.12-slim
  // WORKDIR /app

  // COPY requirements.txt .
  // RUN pip install --no-cache-dir -r requirements.txt

  // COPY . .
  // EXPOSE 8000

  // HEALTHCHECK --interval=30s --timeout=5s \\
  //     CMD python -c "import httpx; httpx.get('http://localhost:8000/api/health').raise_for_status()"

  // CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]`,
  //       highlights: [
  //         '**HEALTHCHECK** — orchestrators use this to route traffic only to healthy instances.',
  //         '**Slim base image** — smaller attack surface, faster builds.',
  //         'Copy requirements first — Docker caches the layer, rebuilds only when deps change.',
  //       ],
  //     },
  //   },

  // --- Cloud production ---

  {
    type: 'title',
    content: {
      title: 'Cloud production',
      subtitle: 'Map patterns to your provider',
      icon: 'globe',
    },
  },
  {
    type: 'three-way',
    content: {
      title: 'Production patterns at a glance',
      left: {
        label: 'AWS',
        items: [
          '**API** — App Runner, ECS Fargate',
          '**Secrets** — Secrets Manager, SSM',
          '**Logs / trace** — CloudWatch, X-Ray',
          '**Managed LLM** — Amazon Bedrock',
          '**Cost** — AWS Budgets, quotas',
        ],
      },
      middle: {
        label: 'Azure',
        items: [
          '**API** — Container Apps, App Service',
          '**Secrets** — Key Vault',
          '**Logs / trace** — App Insights, Monitor',
          '**Managed LLM** — Azure OpenAI',
          '**Cost** — Cost Management, AOAI quotas',
        ],
      },
      right: {
        label: 'GCP',
        items: [
          '**API** — Cloud Run, GKE',
          '**Secrets** — Secret Manager',
          '**Logs / trace** — Cloud Logging, Trace',
          '**Managed LLM** — Vertex AI',
          '**Cost** — Billing budgets, quotas',
        ],
      },
    },
  },
  {
    type: 'title',
    content: {
      title: 'AWS',
      subtitle: 'Enterprise AI on the most common cloud',
      icon: 'server',
    },
  },
  {
    type: 'description',
    content: {
      title: 'When teams choose AWS',
      description:
        '**AWS** is used when an organisation already runs on Amazon infrastructure or needs broad service coverage and compliance programs. For AI production you keep the same patterns from this module — trace IDs, retries, budgets — but wire them to **CloudWatch**, **Secrets Manager**, and optionally **Bedrock** instead of calling OpenAI directly. You deploy your FastAPI image to **App Runner** or **Fargate** and inject secrets at runtime, not in the Docker image.',
      icon: 'server',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'AWS service mapping',
      icon: 'server',
      points: [
        '**Run container** — App Runner (simplest) or ECS Fargate for a FastAPI image.',
        '**Secrets** — Secrets Manager or SSM Parameter Store for `OPENAI_API_KEY`; never bake into the image.',
        '**Tracing** — JSON logs with `trace_id` → CloudWatch Logs; optional X-Ray or ADOT OpenTelemetry.',
        '**Managed LLM** — Amazon Bedrock when policy requires models inside your AWS account.',
        '**Cost** — AWS Budgets + service quotas; align with in-app `CostTracker` session/daily limits.',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Azure',
      subtitle: 'Microsoft cloud + Azure OpenAI',
      icon: 'globe',
    },
  },
  {
    type: 'description',
    content: {
      title: 'When teams choose Azure',
      description:
        '**Azure** fits Microsoft-centric enterprises: Entra ID, existing subscriptions, and **Azure OpenAI Service** for GPT models behind a private endpoint. Production AI apps use **Container Apps** or **App Service** for the FastAPI container, **Key Vault** for API keys, and **Application Insights** for the same span JSON you log in `TraceContext`. The course code stays portable Python; on Azure you swap the OpenAI client endpoint and deployment name while keeping tracing and cost patterns unchanged.',
      icon: 'globe',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Azure service mapping',
      icon: 'globe',
      points: [
        '**Run container** — Azure Container Apps (scale-to-zero) or App Service with Linux containers.',
        '**Secrets** — Key Vault references injected as env vars into Container Apps / App Service.',
        '**Tracing** — Application Insights ingests structured logs and dependency spans.',
        '**Managed LLM** — Azure OpenAI: resource endpoint + deployment name (not raw api.openai.com).',
        '**Cost** — Cost Management budgets; AOAI TPM/RPM quotas mirror token budget enforcement.',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Deploying to Google Cloud',
      subtitle: 'Hosting, data, security, and the model in one project',
      icon: 'globe',
    },
  },
  {
    type: 'description',
    content: {
      title: 'When teams choose Google Cloud',
      description:
        '**Google Cloud** fits a container-native API: **Cloud Run** runs one Docker image, and **Vertex AI** hosts Gemini and other models in-region. The patterns from this module stay the same. `TraceContext` JSON goes to **Cloud Logging**, keys live in **Secret Manager**, and latency goes to **Cloud Trace**. The Dockerfile from the deployment section maps onto Cloud Run: one service, env config, and `/health` for the probe.',
      icon: 'globe',
    },
  },

  {
    type: 'standard',
    content: {
      title: 'Google Cloud: Hosting',
      icon: 'server',
      points: [
        '**Cloud Run** — one container behind an HTTPS URL. Scales to zero, billed per request. Best fit for the FastAPI image in this module.',
        '**Cloud Run functions** — one function for a small job: an event, a queue message, or a schedule. Not the place for the whole API.',
        '**GKE** — Kubernetes. Many services, GPUs, custom networking, and sidecars. You run the node pools. Choose it when a Cloud Run limit binds.',
        '**Compute Engine** — a virtual machine. Use it for a box you log into, or a GPU that is not part of a cluster.',
      ],
    },
  },

  {
    type: 'standard',
    content: {
      title: 'Google Cloud: AI friendly Databases',
      icon: 'database',
      points: [
        '**Vertex AI Vector Search** — a RAG index you own. A local Chroma directory does not survive a new Cloud Run instance.',
        '**Cloud Storage** — source documents, prompt files, and golden eval sets the index was built from.',
        '**Memorystore** — a shared cache of embeddings and model answers, so a repeated query does not call the model again.',
        '**Firestore** — conversation memory and agent checkpoints. **Cloud SQL** with **pgvector** when those records must join to eval rows.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Google Cloud: Vector stores',
      icon: 'database',
      points: [
        '**RAG Engine, managed** — the default. Google stores the embeddings with the corpus. You do not create an index.',
        '**Vertex AI Vector Search** — an index you own. Use it for scale, metadata filters, or hybrid keyword and vector search. This is the replacement for Chroma on the container.',
        '**pgvector on Cloud SQL or AlloyDB** — the embedding sits on the same row as the citation and any SQL filter. Choose it when retrieval is vectors plus a WHERE clause.',
        '**An index you already run** — RAG Engine can query Pinecone or Weaviate. **Vertex AI Search** is the other end: you upload documents and never handle the vectors.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Google Cloud: LLM services',
      icon: 'brain',
      points: [
        '**Gemini** — Google models behind a managed API. Prompt in, text out. No GPU to run.',
        '**Model Garden** — the catalog. Gemini and Gemma, partner models such as Claude and Mistral, and open models such as Llama.',
        '**Model as a Service** — partner and open models on a managed API. Same call shape as Gemini. You do not deploy them.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Google Cloud: Security',
      icon: 'shield',
      points: [
        'One **service account** per service. Grant the roles it needs. Do not download a JSON key.',
        '**Secret Manager** holds API keys and `DATABASE_URL`. Inject them with `--set-secrets`.',
        '**Artifact Registry** stores the image and can scan it on push. The build never sees the secrets.',
        '**Cloud SQL**, **Memorystore**, and Vector Search stay on private IP. Cloud Run reaches them with **Direct VPC egress**. Add **Cloud Armor** if the API is on the public internet.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Google Cloud: Logs, traces, and cost',
      icon: 'search',
      points: [
        'Write JSON to stdout. **Cloud Logging** collects it. No agent in the image.',
        'Every line carries `trace_id` from `TraceContext`, so Logs Explorer can isolate one request.',
        '**Cloud Trace** shows latency across retrieve, model, and guardrail. Export OpenTelemetry if the spans already exist.',
        '**Billing budgets** and Vertex quotas sit beside `CostTracker`. The app cap and the project cap are different limits.',
      ],
    },
  },

  // --- Summary ---

  {
    type: 'rules',
    content: {
      title: 'Summary',
      rules: [
        {
          rule: 'Trace every request',
          example: 'A trace ID is cheap. Debugging without one is expensive.',
          icon: 'search',
        },
        {
          rule: 'Retry with backoff, then fall back',
          example:
            'Jitter stops a thundering herd. A cheaper model or a cache is still an answer.',
          icon: 'refresh-cw',
        },
        {
          rule: 'Budget tokens before you spend them',
          example:
            'Track per-session and per-day. Check the cap before the call, not after the bill.',
          icon: 'list',
        },
        {
          rule: 'Config and secrets stay out of the code',
          example:
            'Environment variables or a secrets manager. A health check for the container.',
          icon: 'shield',
        },
      ],
    },
  },

  {
    type: 'title',
    content: {
      title: 'Module 12 — Complete',
      subtitle: 'Next: Module 13 — Edge Topics',
      icon: 'check-circle',
    },
  },
];
