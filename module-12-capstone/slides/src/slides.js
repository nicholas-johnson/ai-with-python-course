export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 12 — Capstone Project',
      subtitle: 'Full stack agentic ops for the DSS Pathfinder',
      icon: 'rocket',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'All systems integrated',
      points: [
        'Everything you built — agent core, RAG, MCP tools, multi-agent — comes together.',
        'Production hardening: tracing, reliability patterns, cost controls, deployment.',
        'Demo scenarios, integration tests, and an extension checklist for the future.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Build a **full agentic app**: chat + RAG + MCP tools + multi-agent coordination.',
        'Harden for production: **tracing**, **retries**, **circuit breakers**, **cost controls**.',
        'Write **demo scenarios** that show value to mission operations.',
        'Add **integration tests** and document **extension points**.',
        '**Containerise and deploy** with Docker, env config, and health checks.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Architecture overview',
      icon: 'layers',
      points: [
        '**Chat interface**: CLI or API — user sends questions, gets answers.',
        '**RAG pipeline**: ship logs, manuals, and star charts indexed and searchable.',
        '**MCP tool suite**: sensor reads, crew lookups, log queries.',
        '**Multi-agent path**: router → specialist → critic for complex questions.',
        '**Production layer**: tracing, retries, circuit breakers, cost tracking.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Capstone app skeleton',
      code: `class PathfinderAgent:
    def __init__(self, llm, tools, retriever, agents):
        self.llm = llm
        self.tools = tools
        self.retriever = retriever
        self.agents = agents
        self.memory = SessionMemory()

    def chat(self, user_input: str) -> str:
        self.memory.add({"role": "user", "content": user_input})

        if needs_retrieval(user_input):
            context = self.retriever.search(user_input)
        if needs_specialist(user_input):
            return self.agents.route(user_input)

        response = self.llm.chat(self.memory.get_messages())
        self.memory.add({"role": "assistant", "content": response})
        return response`,
      highlights: [
        'Decides per-query: direct answer, retrieval, or multi-agent',
        'Session memory persists across the conversation',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Structured tracing',
      icon: 'search',
      points: [
        'Every request gets a **trace ID** — a UUID that propagates through every step.',
        'Each step is a **span** with timing, status, and metadata.',
        'Log spans as JSON — send to Datadog, Jaeger, or OpenTelemetry in production.',
        'Never log secrets or full payloads — use safe previews only.',
        'A trace ID is cheap; **debugging without one is expensive**.',
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
        self.spans = []

    def start_span(self, name):
        span = {
            "span_id": str(uuid.uuid4()),
            "trace_id": self.trace_id,
            "name": name,
            "start_time": time.time(),
        }
        self.spans.append(span)
        return span

    def end_span(self, span, status="ok", metadata=None):
        span["duration_ms"] = (time.time() - span["start_time"]) * 1000
        span["status"] = status`,
      highlights: [
        'Trace ID links every span in a single request',
        'Duration in milliseconds for performance analysis',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Reliability patterns',
      icon: 'shield',
      points: [
        '**Retries with backoff**: exponential delay + jitter to avoid thundering herds.',
        '**Timeouts**: 30s for LLM, 5s for tools, 2s for DB — never wait forever.',
        '**Circuit breaker**: stop hammering a failing service — fail fast after threshold.',
        '**Fallbacks**: primary model → cheaper model → cached response → error message.',
        'Only retry **transient** errors (5xx, timeout) — never retry 4xx.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Circuit breaker pattern',
      code: `class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_time=60):
        self.failures = 0
        self.threshold = failure_threshold
        self.state = "closed"  # closed → open → half-open

    async def call(self, fn):
        if self.state == "open":
            if time.time() - self.last_failure > self.recovery_time:
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
            if self.failures >= self.threshold:
                self.state = "open"
            raise`,
      highlights: [
        'Three states: closed (normal), open (rejecting), half-open (testing)',
        'After recovery_time, one test request decides next state',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Cost controls',
      icon: 'dollar-sign',
      points: [
        '**Token budgets**: track per-session and per-day usage, reject when exceeded.',
        '**Model tiering**: route simple queries to cheap models, complex to expensive.',
        '**Caching**: exact-match or semantic — skip the API call entirely.',
        '**Batching**: group small requests into one call to reduce overhead.',
        'The biggest cost lever is **model tiering** — classification is cheap.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Deployment essentials',
      icon: 'package',
      points: [
        '**Environment config**: settings from env vars, not hard-coded values.',
        '**Secrets management**: API keys in env vars or a secrets manager — never in code.',
        '**Docker**: Dockerfile packages app + deps for consistent deployment.',
        '**Health checks**: `/health` endpoint returns 200 when ready — orchestrators use this.',
        '**Twelve-Factor App**: one codebase, config in env, stateless processes.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Demo scenarios',
      icon: 'play',
      points: [
        '**Simple Q&A**: "Who is the chief engineer?" → direct tool call.',
        '**RAG query**: "What happened during the Kepler Sweep?" → retrieval + grounded answer.',
        '**Multi-step**: "Compare hull integrity reports from last week" → decompose + retrieve + synthesise.',
        '**Multi-agent**: "Plan a rescue mission" → router → researcher → critic → final plan.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Integration testing',
      icon: 'check-square',
      points: [
        '**Happy path**: known question → expected tool calls → correct answer.',
        '**Failure path**: tool timeout → graceful fallback, not a crash.',
        '**Adversarial**: question with no answer → "I don\'t know", not a hallucination.',
        '**Mock the LLM** for deterministic tests; test with a live model separately.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Integration test structure',
      code: `def test_crew_query(agent, mock_llm):
    mock_llm.set_response(
        tool_calls=[{"name": "query_crew",
                      "arguments": {"department": "science"}}],
        final="3 crew in science: Voss, Chen, Morel.",
    )
    result = agent.chat("Who is in the science team?")

    assert "Voss" in result
    assert mock_llm.tool_calls_made == ["query_crew"]

def test_unknown_question(agent, mock_llm):
    mock_llm.set_response(
        final="I don't have enough information to answer."
    )
    result = agent.chat("What is the meaning of life?")
    assert "don't have" in result.lower()`,
      highlights: [
        'Mock LLM makes tests fast, free, and deterministic',
        'Test both success paths and graceful failure',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Extension checklist',
      icon: 'plus-square',
      points: [
        '**New tool**: add to the MCP server → update tool registry → write tests.',
        '**New data source**: chunk → embed → add to vector index → test retrieval.',
        '**New agent role**: define system prompt → register in router → test routing.',
        '**New policy**: add guardrail to the chain → test with adversarial inputs.',
        'Document each extension point so future engineers know where to plug in.',
      ],
    },
  },
  {
    type: 'comparison',
    content: {
      title: 'What you built over 3 days',
      left: {
        label: 'Day 1',
        items: [
          'Python fundamentals',
          'Agent core + tool loop',
          'LLM integration + streaming',
          'Prompt engineering + guardrails',
        ],
      },
      right: {
        label: 'Days 2-3',
        items: [
          'MCP server + tools',
          'RAG + knowledge graphs',
          'Multi-agent + memory',
          'LangChain + production + capstone',
        ],
      },
    },
  },
  {
    type: 'rules',
    content: {
      title: 'Field rules — Capstone',
      rules: [
        {
          rule: 'Integration tests are not optional',
          example: 'The capstone must prove it works — demos and assertions.',
          icon: 'check-square',
        },
        {
          rule: 'Trace every request',
          example: 'A trace ID is cheap; debugging without one is expensive.',
          icon: 'search',
        },
        {
          rule: 'Never hard-code secrets',
          example: 'Environment variables or a secrets manager — nothing else.',
          icon: 'lock',
        },
        {
          rule: 'Ship it',
          example: 'A working demo beats a perfect plan. Launch, then iterate.',
          icon: 'rocket',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises — Final mission',
      points: [
        '01 — Capstone app: integrated chat + RAG + MCP + multi-agent with tracing',
        '02 — Harden and deploy: reliability patterns, cost controls, Docker container',
        '03 — Test and extend: integration tests + extension documentation',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Mission complete — Module 12',
      subtitle: 'The Pathfinder AI is online. Well done, Engineer.',
      icon: 'party-popper',
    },
  },
];
