# MSCI — AI Engineering with Python

**Three-day outline** (Modules 1–13; Module 0 skipped)

**Mission:** Build production-grade AI systems — agents, tools, RAG pipelines, and multi-agent workflows — in Python.

---

## Day 1 — Build a working agent

**Theme:** From first LLM call to a full Research Assistant web app — chat, tools, MCP, and multimodal.

| Block | Module | Topic |
| ----- | ------ | ----- |
| 1 | Working with the LLM | Chat APIs, streaming, prompting |
| 2 | Tool Calling | Agent loop, registry, safety rails |
| 3 | MCP Server | Protocol, MCPServer, stdio & HTTP |
| 4 | GenAI Strategies | Research Assistant (Day 1 closer) |

---

### Module 1 — Working with the LLM

**Talk**

- Chat-completion API: message roles, parameters, responses
- Conversation history and context windows
- Streaming for perceived latency
- Prompt engineering: persona, format constraints, guardrails, few-shot

**Demo**

- Interactive walkthrough: basic chat → streaming → prompting patterns (`demo/demo.py`)

**Exercises**

1. **First chat** — First LLM API call and interactive console chat loop
2. **Streaming** — Stream responses token by token
3. **Prompting** — System prompts for persona, format, guardrails, and few-shot

**After this module, attendees can**

- Call an LLM API from Python and maintain a multi-turn chat
- Stream tokens to a CLI in real time
- Write production-minded prompts that control persona, format, and scope

---

### Module 2 — Tool Calling

**Talk**

- Message format and conversation state (system / user / assistant / tool)
- The tool-calling loop: schema in → action → result → repeat
- Tool registry: decorator registration, JSON Schema, validation, routing
- Safety rails: allowlists, rate limits, redaction, audit logs
- Golden-file / mock eval for regression testing

**Demo**

- Four-part interactive demo: message format → registry → safety rails → eval harness

**Exercises**

1. **Tool-calling agent** — Agent loop with real OpenAI tool calls
2. **Tool registry** — Decorator-based registry plugged into the agent
3. **Guarded agent** — Allowlist, rate limiter, and audit log around the agent

**After this module, attendees can**

- Build a capped tool-calling agent from scratch
- Register and validate tools with a reusable registry
- Harden an agent with allowlists, rate limits, and audit trails

---

### Module 3 — MCP Server

**Talk**

- Model Context Protocol: discovery, schemas, calling conventions
- Host vs server vs transport (stdio, HTTP+SSE)
- MCPServer (formerly FastMCP): tools from type hints and docstrings
- Practical tools: sensors, crew lookup, log search
- MCP client patterns and OpenAI tool-format conversion

**Demo**

- Concepts → MCPServer → live client + tool-calling agent loop

**Exercises**

1. **Local MCP server** — Stdio MCPServer (power grid tools) for a provided agent harness
2. **HTTP MCP server** — Streamable-HTTP server (science lab tools) at a URL
3. **Ship docs** — MCP resources + search/read tools over ship documentation

**After this module, attendees can**

- Explain MCP and when to use it vs hard-coded tools
- Build MCP servers with `MCPServer` over stdio and HTTP
- Expose data as tools and resources that agents discover dynamically

---

### Module 4 — GenAI Strategies *(Day 1 closer)*

**Talk**

- Assembling Modules 1–3 into a real web app
- Model selection: quality vs cost vs latency
- Token counting and context budgets (`tiktoken`)
- Multimodal: vision (GPT-6 Luna), audio (gpt-transcribe)
- Guardrails: schema validation, content filters, confidence thresholds

**Demo**

- Vision analysis and speech-to-text on sample media

**Exercises**

1. **Research chat** — FastAPI + SSE streaming chat with MCP tool calling (server provided; Svelte frontend lights up as endpoints ship)
2. **Multimodal** — `/vision` and `/transcribe` endpoints

**After this module, attendees can**

- Ship a streaming chat backend with MCP tools behind a web UI
- Reason about model choice and token budgets
- Add vision and speech-to-text to an AI API
- Apply layered guardrails on model output

---

### Day 1 outcomes

By end of day, attendees can build a **tool-using agent**, expose capabilities via **MCP**, and deliver a **streaming Research Assistant** with multimodal endpoints.

---

## Day 2 — Knowledge + retrieval

**Theme:** Ground agents in documents and structured facts; add memory and deliberate workflows.

| Block | Module | Topic |
| ----- | ------ | ----- |
| 5 | RAG Fundamentals | Chunk, embed, retrieve, cite |
| 6 | Structured Facts | Extraction, knowledge graphs, grounded QA |
| 7 | Agent Memory | Session / long-term memory, summarisation |
| 8 | Structured Workflows | ReAct, plan-and-execute (Day 2 closer) |

---

### Module 5 — RAG Fundamentals

**Talk**

- RAG pipeline: chunk → embed → store → retrieve → generate
- Chunking: fixed-size, sentence-aware, structure-aware, overlap, metadata
- Embeddings (`text-embedding-3-small`) and vector stores (ChromaDB; FAISS noted)
- Grounded prompts with `[Source N]` citations

**Demo**

- Multi-step ChromaDB walkthrough: ingest → optional MCP inspect → chat with RAG agent (Docker Compose)

**Exercises**

1. **Build the index** — Chunk ship logs, embed, store in ChromaDB, interactive search
2. **RAG chat** — Grounded chat with citations and `/norag` comparison
3. **RAG MCP server** — Wrap RAG as MCP tools for a tool-calling agent

**After this module, attendees can**

- Build an end-to-end RAG index and search over documents
- Answer questions with grounded citations
- Expose retrieval as MCP tools for any agent

---

### Module 6 — Structured Facts

**Talk**

- Why structured outputs beat free text for verification
- Pydantic schemas and structured extraction
- Fact pipeline: extract → validate (confidence) → store
- Knowledge graphs with `networkx` (entities, relationships, traversal)
- Grounded QA from graph evidence

**Demo**

- Three scripts: extraction → graph build/query → graph-grounded QA vs ungrounded

**Exercises**

1. **Fact extractor** — Structured facts from ship logs (Pydantic + OpenAI)
2. **Knowledge graph** — Build and query a networkx graph interactively
3. **Grounded QA** — Answers with `[Fact N]` citations from graph evidence

**After this module, attendees can**

- Extract typed facts with confidence and provenance
- Organise facts into a queryable knowledge graph
- Answer questions only when graph evidence supports them

---

### Module 7 — Agent Memory

**Talk**

- Memory as external storage + prompt injection (LLMs are otherwise stateless)
- Short-term session buffers vs long-term profiles
- Decay and “do not remember” / forget controls
- Summarisation to fit token budgets
- Memory as MCP tools

**Demo**

- Session memory → long-term remember/recall/decay/forget → summarisation → memory-enhanced chat

**Exercises**

1. **Memory store** — Session + long-term memory with decay/forget, wired into a chat agent
2. **Conversation summary** — Auto-summarise long conversations under a token budget
3. **Memory MCP server** — Expose memory over MCP stdio for agent use

**After this module, attendees can**

- Design short- and long-term memory for agents
- Summarise history instead of silently truncating
- Honour privacy forget requests and expose memory via MCP

---

### Module 8 — Structured Workflows *(Day 2 closer)*

**Talk**

- ReAct: Thought → Action → Observation with traces
- Plan-and-execute: plan up front, execute, re-plan on failure
- When to use each (exploration vs structured multi-step tasks)
- Streaming and plan visualisation in a web app

**Demo**

- Live ReAct loop with tools; plan-and-execute with re-planning on failure

**Exercises**

1. **ReAct agent** — ReAct loop with web search, calculator, notes + full trace
2. **Plan-and-execute** — Planner + executor with re-planning; compare to ReAct
3. **Holiday planner** — FastAPI + Svelte app with plan visualisation (frontend provided)

**After this module, attendees can**

- Implement ReAct and plan-and-execute with capped loops and traces
- Choose the right workflow pattern for a task
- Integrate structured workflows into a streaming web UI

---

### Day 2 outcomes

By end of day, attendees can ground answers in **RAG and knowledge graphs**, give agents **durable memory**, and run **structured multi-step workflows** (including a Holiday Planner app).

---

## Day 3 — Ship it

**Theme:** Multi-agent systems, framework acceleration, evaluation, production hardening with a capstone, and optional edge techniques.

| Block | Module | Topic |
| ----- | ------ | ----- |
| 9 | Multi-Agent Systems | Roles, coordination, consensus |
| 10 | LangChain with Python | LCEL, agents, RAG, serving chains |
| 11 | Evals | Golden tests, retrieval metrics, LLM-as-judge, faithfulness, gate |
| 12 | Productionisation | Hardening + capstone apps |
| 13 | Edge Topics | Advanced RAG & production techniques (pick-and-choose) |

---

### Module 9 — Multi-Agent Systems

**Talk**

- When multi-agent helps vs when a single agent is enough
- Roles: router, researcher, critic, supervisor, executor
- Patterns: supervisor, debate, swarm/handoff, shared context
- Consensus and conflict resolution; scoped tools per role

**Demo**

- Interactive multi-agent coordination walkthrough (`demo/demo.py`)

**Exercises**

1. **Router agent** — Route to medical / tactical / comms specialists
2. **Supervisor-critic** — Supervisor + specialists + critic revision loop
3. **Consensus** — Debate, judge synthesis, consensus voting
4. **Swarm tools** — Scoped tools and peer-to-peer `transfer_to_*` handoffs

**After this module, attendees can**

- Design multi-agent architectures with clear roles and tool scopes
- Implement router, supervisor-critic, debate/consensus, and swarm handoffs
- Decide when multi-agent complexity is justified

---

### Module 10 — LangChain with Python

**Talk**

- LangChain building blocks: prompts, models, parsers
- LCEL (`|`) for composable, streamable, batchable chains
- Tool agents via `create_agent` (LangChain 1.x)
- RAG chains with retrievers
- Serving chains with FastAPI
- When to use the framework vs stay hand-rolled

**Demo**

- Chains & prompts → agents → RAG → serving a chain with FastAPI

**Exercises** *(CSS Horizon scenario — apply patterns, not copy Pathfinder demos)*

1. **Chain basics** — LCEL report classifier (category, summary, priority)
2. **Tool agent** — Classifier + ship tools with `create_agent`
3. **RAG chain** — Retrieval over ship logs on top of the agent
4. **Chain API** — Expose the classifier via FastAPI

**After this module, attendees can**

- Assemble LCEL chains, tool agents, and RAG with LangChain
- Deploy a chain as a REST API with FastAPI
- Judge when LangChain speeds them up vs when plain Python is clearer

---

### Module 11 — Evals

**Talk**

- Why a live demo is not an eval: frozen test sets, CI vs token spend
- Golden-file tests: mock the LLM, run the real agent loop, assert tools + answer
- Retrieval metrics: recall@k, precision@k, MRR on a labelled query set
- LLM-as-judge: correctness, completeness, relevance (JSON, temperature 0)
- Faithfulness: every claim grounded in retrieved context
- Scorecard + gate: pick a winner, fail a release below a floor

**Demo**

- Five-part walkthrough, no API key (`demo/demo.py`): golden tests, retrieval metrics, judge, faithfulness, scorecard + gate

**Exercises**

1. **Golden tests** — Mock-LLM agent loop, score tools + answer, run a suite
2. **Retrieval metrics** — recall@k, precision@k, MRR on labelled ship-log queries
3. **LLM-as-judge** — Correctness, completeness, relevance
4. **Faithfulness** — Claim extraction + support check + ratio
5. **Eval compare** — Scorecard two configs, pick a winner, gate a release

**After this module, attendees can**

- Regression-test a tool-calling agent without an API key
- Score retrieval and generation with labelled sets and an LLM judge
- Compare two pipeline configs and fail a release that drops below a floor

---

### Module 12 — Productionisation *(capstone)*

**Talk**

- Structured tracing (trace IDs, spans, JSON logs)
- Reliability: retries with backoff/jitter, timeouts, circuit breakers, fallbacks
- Cost controls: budgets, model tiering, caching, batching
- Deployment: env config, secrets, Docker, health checks

**Demo**

- Tracing, circuit breaker, and cost-control scripts

**Exercises** *(choose one full-stack capstone — frontend provided; build FastAPI backend)*

| App | Techniques practised |
| --- | -------------------- |
| **Recipe Finder** | RAG, hybrid search, reranking, multimodal vision, allergen guardrails |
| **Movie Night** | RAG, hybrid search, text-to-SQL, structured output |
| **Travel Planner** | Agentic RAG, tool calling, structured itineraries, web fallback |
| **Personal Assistant** | Chat + tools + MCP, RAG over notes, calendar, cost controls |

**After this module, attendees can**

- Add tracing, retries, circuit breakers, and cost budgets to an AI service
- Configure secrets and health checks for deployment
- Ship a production-minded FastAPI backend for a real product UI using course techniques

---

### Module 13 — Edge Topics

**Talk** *(pick-and-choose; slide deck covers ~16 concepts)*

Core hands-on themes typically include:

- Hybrid search (RRF), re-ranking, HyDE
- Agentic RAG, citation verification
- Text-to-SQL (LLM-as-judge lives in Module 11)
- Guardrails, semantic caching
- Multimodal RAG, contextual chunking
- Concepts-only: test-time compute, speculative decoding, GraphRAG, DPO/LoRA, MoE
- Optional: local CPU training & Hugging Face Hub inference

**Demo**

- Hybrid search, agentic RAG, citation verification, semantic cache
- Optional: local DistilBERT training and Hugging Face sentiment pipeline

**Exercises**

Independent labs — attendees choose by interest/time, e.g.:

| Focus | Examples |
| ----- | -------- |
| Retrieval quality | Hybrid search, re-ranking, HyDE, contextual chunking |
| Agentic / trust | Agentic RAG, citation verification, web search backend |
| Data | Text-to-SQL, fine-tuning data prep |
| Production UX | Guardrails, semantic cache, multimodal RAG |
| Local ML | Local training, Hugging Face run |

**After this module, attendees can**

- Apply at least one advanced retrieval or reliability technique to a RAG/agent system
- Name trade-offs for hybrid search, re-ranking, agentic RAG, caching, and guardrails
- Optionally train/run a small model on CPU without a cloud GPU

---

### Day 3 outcomes

By end of day, attendees can coordinate **multi-agent** systems, accelerate with **LangChain**, **evaluate** agents and RAG, harden a **capstone app** for production, and optionally apply **advanced RAG/ops techniques**.

---

## At a glance

| Day | Modules | Closer | Attendees leave able to… |
| --- | ------- | ------ | ------------------------ |
| **1** | 1–4 | Research Assistant | Call LLMs, build tool agents, serve MCP, ship a streaming multimodal chat API |
| **2** | 5–8 | Holiday Planner | Ground answers (RAG + graphs), manage agent memory, run ReAct / plan-and-execute workflows |
| **3** | 9–13 | Capstone app | Orchestrate multi-agent systems, use LangChain, evaluate pipelines, productionise and ship, pick edge techniques |

---

## Prerequisites (for MSCI delivery)

- Python 3.12+, pip, virtualenv
- Node.js v20+ and pnpm (slides / frontends)
- OpenAI API key (or compatible provider)
- Code editor (VS Code / Cursor recommended)
