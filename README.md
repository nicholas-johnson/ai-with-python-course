# Deep Space Ops: AI Engineering with Python

```
        *    .  *       .             *
   *  .    ___|___    *    .   *
     .    /  DSS  \      .        *
  *      | Pathfinder|  .     *
   .      \___|___/    *   .
     *    .' | | `.         .    *
  .      /   | |   \   *      .
        *    * *    .      *
   Welcome aboard, Engineer.
```

**Mission:** Build production-grade AI systems — agents, tools, RAG pipelines, and multi-agent workflows — while running everything in **Python**. The DSS Pathfinder needs her AI subsystems online before we reach uncharted sectors. You have three days.

## Prerequisites

- **Python** 3.12 or newer (`python --version`)
- **uv** (recommended) or **pip** — install uv with `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Node.js** v20+ and **pnpm** v10+ (for slides only) — `corepack enable && corepack prepare pnpm@latest --activate`
- A code editor (VS Code / Cursor recommended)
- An OpenAI API key (or compatible provider) in your environment

## Setup

```bash
cd ai-python-course

# Python dependencies
uv sync                     # or: pip install -e ".[dev]"

# Slides dependencies (pnpm monorepo)
pnpm install

# Run all exercise tests (many fail until you complete start.py)
pytest

# Run tests for a single module
pytest module-01-python-fundamentals/

# Run a single exercise's tests
pytest module-01-python-fundamentals/exercises/01-dataclass-filtering/test_start.py
```

## Project structure

This is a **hybrid monorepo** — Python exercises and demos live alongside a pnpm workspace that powers the slide decks.

Each **module** has its own `README.md`, **demo** scripts you can run with `python …`, and **exercises** with `start.py` (your work), `test_start.py` (pytest), and `solution.py` (instructor reference — try the exercise first!).

Shared mission data lives in [`data/`](data/).

## Slides

Each module includes a Vite app under `slides/` that renders teaching decks with the workspace package [`slide-deck`](slide-deck/).

```bash
pnpm slides:01          # same pattern :02 … :13
# or
cd module-01-python-fundamentals/slides && pnpm dev
```

## Schedule

### Day 1 — Build a working chatbot

| Block | Module | Topic |
| ----- | ------ | ----- |
| 1 | [module-01-python-fundamentals](module-01-python-fundamentals/) | Data structures, modules, CLI, logging, async, HTTP |
| 2 | [module-02-agent-core](module-02-agent-core/) | Message format, tool registry, safety rails, eval harness |
| 3 | [module-03-working-with-the-llm](module-03-working-with-the-llm/) | LLM APIs, chat integration, streaming, prompting patterns |
| 4 | [module-04-genai-strategies](module-04-genai-strategies/) | Conversational AI, prompt engineering, multimodal, guardrails |

### Day 2 — MCP + knowledge

| Block | Module | Topic |
| ----- | ------ | ----- |
| 5 | [module-05-mcp-server](module-05-mcp-server/) | MCP concepts, build a server, practical tools, auth |
| 6 | [module-06-rag-fundamentals](module-06-rag-fundamentals/) | Chunking, embeddings, vector stores, retrieval, evaluation |
| 7 | [module-07-multi-agent](module-07-multi-agent/) | Roles, coordination patterns, shared context |
| 8 | [module-08-agent-memory](module-08-agent-memory/) | Short/long-term memory, summarisation, ReAct, plan-and-execute |

### Day 3 — Structured knowledge + ship it

| Block | Module | Topic |
| ----- | ------ | ----- |
| 9 | [module-09-structured-facts](module-09-structured-facts/) | Structured outputs, fact extraction, knowledge graphs, grounded QA |
| 10 | [module-10-adaptive-retrieval](module-10-adaptive-retrieval/) | Retrieval routing, self-critique, query decomposition, multi-source QA |
| 11 | [module-11-production](module-11-production/) | Tracing, reliability, cost controls, deployment |
| 12 | [module-12-langchain](module-12-langchain/) | Chains, agents, tools, RAG — framework-powered AI |
| 13 | [module-13-capstone](module-13-capstone/) | Full agentic app: chatbot + RAG + MCP + multi-agent |

## Course outline

All **exercises** run in **Python** and are checked with **pytest** (`start.py` / `test_start.py`). **Demos** are plain `python …` scripts. Optional **slides** under each module's `slides/` folder are separate Vite + React apps for teaching only.

### Module 1 — [Python Fundamentals](module-01-python-fundamentals/)

**Topics:** Data structures (lists, dicts, sets, tuples), modules/packages, CLI args, logging, dataclasses, Protocols, asyncio (tasks, queues, timeouts, cancellation), HTTP basics with FastAPI and httpx.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Dataclass filtering | [`exercises/01-dataclass-filtering`](module-01-python-fundamentals/exercises/01-dataclass-filtering/) | Parse/filter/transform crew JSON with dataclasses, CLI args |
| Async queue processing | [`exercises/02-async-queue-processing`](module-01-python-fundamentals/exercises/02-async-queue-processing/) | Async queue processing ship sensor data with timeouts |
| FastAPI CRUD | [`exercises/03-fastapi-crud`](module-01-python-fundamentals/exercises/03-fastapi-crud/) | FastAPI CRUD for missions with httpx test client |

### Module 2 — [Agent Core](module-02-agent-core/)

**Topics:** Message format + state, tool registry pattern (schema, validation, routing, error handling), safety rails (allowlists, rate limits, redaction, audit logs), evaluation harness (golden tests, replay, deterministic mocks).

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Tool loop | [`exercises/01-tool-loop`](module-02-agent-core/exercises/01-tool-loop/) | Minimal tool-calling loop: schema in, action out, result back |
| Tool registry | [`exercises/02-tool-registry`](module-02-agent-core/exercises/02-tool-registry/) | Registry with validation and routing |
| Safety + eval | [`exercises/03-safety-eval`](module-02-agent-core/exercises/03-safety-eval/) | Rate limiting + golden-file tests for a tool agent |

### Module 3 — [Working with the LLM](module-03-working-with-the-llm/)

**Topics:** LLM API integration (chat completions, message roles, parameters), streaming responses, prompting patterns (structured outputs, grounding, tool calling), building a simple chat interface, session storage.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Chat loop | [`exercises/01-chat-loop`](module-03-working-with-the-llm/exercises/01-chat-loop/) | CLI chatbot with conversation history |
| Streaming API | [`exercises/02-streaming-api`](module-03-working-with-the-llm/exercises/02-streaming-api/) | FastAPI streaming endpoint with SSE |
| Session manager | [`exercises/03-session-manager`](module-03-working-with-the-llm/exercises/03-session-manager/) | Pluggable session backend: in-memory then file-based |

### Module 4 — [Conversational AI + Multimodal](module-04-genai-strategies/)

**Topics:** Prompting patterns that hold up in production (structured outputs, tool calling, grounding), model selection trade-offs (quality/cost/latency), token budgeting, caching, reliability + guardrails (evals, red-teaming, failure modes).

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Structured prompts | [`exercises/01-structured-prompts`](module-04-genai-strategies/exercises/01-structured-prompts/) | Build prompts that produce JSON-parseable outputs |
| Token budget | [`exercises/02-token-budget`](module-04-genai-strategies/exercises/02-token-budget/) | Token counting and budget enforcement |
| Guardrail chain | [`exercises/03-guardrail-chain`](module-04-genai-strategies/exercises/03-guardrail-chain/) | Schema validation, content filter, confidence threshold |
| Multimodal analysis | [`exercises/04-multimodal-analysis`](module-04-genai-strategies/exercises/04-multimodal-analysis/) | Vision and audio payloads, structured damage report parsing |

### Module 5 — [MCP Server](module-05-mcp-server/)

**Topics:** MCP concepts (tool discovery, schemas, calling conventions), building a minimal MCP server, practical tools (filesystem, HTTP fetch, DB query, calculators), auth + permissions, observability, versioning.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Hello MCP | [`exercises/01-hello-mcp`](module-05-mcp-server/exercises/01-hello-mcp/) | Minimal MCP server exposing one tool |
| MCP tools | [`exercises/02-mcp-tools`](module-05-mcp-server/exercises/02-mcp-tools/) | Three ship-system tools: sensor read, crew lookup, log query |
| Auth + observability | [`exercises/03-auth-observability`](module-05-mcp-server/exercises/03-auth-observability/) | Per-tool auth scopes and structured logging |
| MCP client | [`exercises/04-mcp-client`](module-05-mcp-server/exercises/04-mcp-client/) | Build an MCP client: discover tools, validate args, handle errors |

### Module 6 — [RAG Fundamentals](module-06-rag-fundamentals/)

**Topics:** Chunking strategies (size, overlap, structure-aware), embeddings and vector stores (local and managed), retrieval (dense, sparse, hybrid, reranking), grounded prompting with citations, RAG evaluation.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Document chunker | [`exercises/01-document-chunker`](module-06-rag-fundamentals/exercises/01-document-chunker/) | Chunk ship logs into overlapping windows for indexing |
| Vector search | [`exercises/02-vector-search`](module-06-rag-fundamentals/exercises/02-vector-search/) | Embed and search the mission archives |
| RAG pipeline | [`exercises/03-rag-pipeline`](module-06-rag-fundamentals/exercises/03-rag-pipeline/) | End-to-end RAG with citation linking back to sources |

### Module 7 — [Multi-Agent Systems](module-07-multi-agent/)

**Topics:** When multi-agent helps vs hurts, agent roles (router, researcher, coder, critic), coordination patterns (supervisor, swarm, debate, blackboard), shared context and tools, consensus and conflict resolution.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Router agent | [`exercises/01-router-agent`](module-07-multi-agent/exercises/01-router-agent/) | Route queries to navigation, engineering, or science specialists |
| Supervisor-critic | [`exercises/02-supervisor-critic`](module-07-multi-agent/exercises/02-supervisor-critic/) | Supervisor coordinates researcher + critic for mission briefings |
| Consensus | [`exercises/03-consensus`](module-07-multi-agent/exercises/03-consensus/) | Multiple agents propose answers; vote on the best response |

### Module 8 — [Agent Memory + Workflows](module-08-agent-memory/)

**Topics:** Short-term session memory vs long-term profile, summarisation for context limits, decay and "do not remember" controls, workflow patterns (ReAct, plan-and-execute, tool routing).

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Memory store | [`exercises/01-memory-store`](module-08-agent-memory/exercises/01-memory-store/) | Short-term buffer and long-term memory with decay |
| Conversation summary | [`exercises/02-conversation-summary`](module-08-agent-memory/exercises/02-conversation-summary/) | Summarise long conversations to fit a token budget |
| ReAct loop | [`exercises/03-react-loop`](module-08-agent-memory/exercises/03-react-loop/) | Implement ReAct: Reason, Act, Observe |

### Module 9 — [Structured Facts](module-09-structured-facts/)

**Topics:** Structured outputs (Pydantic, JSON Schema), fact extraction pipelines with provenance and confidence, knowledge graph construction (entities, relationships), grounded QA with citations.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Fact extractor | [`exercises/01-fact-extractor`](module-09-structured-facts/exercises/01-fact-extractor/) | Extract structured facts from ship logs using Pydantic schemas |
| Knowledge graph | [`exercises/02-knowledge-graph`](module-09-structured-facts/exercises/02-knowledge-graph/) | Build a graph from entities and query for relationships |
| Grounded QA | [`exercises/03-grounded-qa`](module-09-structured-facts/exercises/03-grounded-qa/) | Answer questions with source citations and confidence scores |

### Module 10 — [Adaptive Retrieval](module-10-adaptive-retrieval/)

**Topics:** Retrieval routing (vector, graph, keyword), query decomposition, self-critique loops (corrective RAG), multi-source orchestration with merge and ranking.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Retrieval router | [`exercises/01-retrieval-router`](module-10-adaptive-retrieval/exercises/01-retrieval-router/) | Route queries to vector, graph, or keyword search |
| Self-critique | [`exercises/02-self-critique`](module-10-adaptive-retrieval/exercises/02-self-critique/) | Evaluate retrieval quality and refine queries |
| Multi-source QA | [`exercises/03-multi-source-qa`](module-10-adaptive-retrieval/exercises/03-multi-source-qa/) | Fan out to multiple backends, merge, rank, answer with citations |

### Module 11 — [Production & Deployment](module-11-production/)

**Topics:** Structured tracing and logging, reliability (retries, circuit breakers, fallbacks), cost controls (budgets, batching, model tiering), environment config, secrets, containers, CI/CD.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Trace middleware | [`exercises/01-trace-middleware`](module-11-production/exercises/01-trace-middleware/) | Add trace IDs and timing to every tool call |
| Batch pipeline | [`exercises/02-batch-pipeline`](module-11-production/exercises/02-batch-pipeline/) | Batch LLM requests with retry and fallback model |
| Cost tracker | [`exercises/03-cost-tracker`](module-11-production/exercises/03-cost-tracker/) | Per-session token and cost budget enforcement |
| Deploy container | [`exercises/04-deploy-container`](module-11-production/exercises/04-deploy-container/) | Health-check app, env config, Dockerfile validation |

### Module 12 — [LangChain with Python](module-12-langchain/)

**Topics:** LangChain vs hand-rolled (chains, agents, tools, memory, output parsers), prompt templates and LCEL, rewriting agent loops with LangChain, connecting to MCP and RAG pipelines.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Chain basics | [`exercises/01-chain-basics`](module-12-langchain/exercises/01-chain-basics/) | Prompt template + chain for crew report classification |
| Tool agent | [`exercises/02-tool-agent`](module-12-langchain/exercises/02-tool-agent/) | Wrap ship tools as LangChain tools, run via AgentExecutor |
| RAG chain | [`exercises/03-rag-chain`](module-12-langchain/exercises/03-rag-chain/) | RetrievalQA chain over the Pathfinder knowledge base |

### Module 13 — [Capstone Project](module-13-capstone/)

**Topics:** Full agentic application integrating chat, RAG, MCP tools, and multi-agent coordination. Demo scenarios, integration tests, extension documentation.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Capstone app | [`exercises/01-capstone-app`](module-13-capstone/exercises/01-capstone-app/) | Integrated chat + RAG + MCP + multi-agent app |
| Test and extend | [`exercises/02-test-and-extend`](module-13-capstone/exercises/02-test-and-extend/) | Integration tests and extension documentation |

## Running tests

```bash
# All exercises
pytest

# One module
pytest module-01-python-fundamentals/

# One exercise
pytest module-01-python-fundamentals/exercises/01-dataclass-filtering/test_start.py

# With verbose output
pytest -v module-02-agent-core/
```

## License

Copyright (c) 2026 Nicholas Johnson. **All rights reserved.** This material is not licensed for use, copying, or distribution by others. See [LICENSE](LICENSE).
