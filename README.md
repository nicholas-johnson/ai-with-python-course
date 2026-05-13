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
pytest module-01-working-with-the-llm/

# Run a single exercise's tests
pytest module-00-python-fundamentals/exercises/01-dataclass-filtering/test_start.py
```

## Project structure

This is a **hybrid monorepo** — Python exercises and demos live alongside a pnpm workspace that powers the slide decks.

Each **module** has its own `README.md`, **demo** scripts you can run with `python …`, and **exercises** with `start.py` (your work), `test_start.py` (pytest), and `solution.py` (instructor reference — try the exercise first!).

Shared mission data lives in [`data/`](data/).

## Slides

Each module includes a Vite app under `slides/` that renders teaching decks with the workspace package [`slide-deck`](slide-deck/).

```bash
pnpm slides:01          # same pattern :00 … :12
# or
cd module-01-working-with-the-llm/slides && pnpm dev
```

## Schedule

### Day 1 — Build a working agent

| Block | Module | Topic |
| ----- | ------ | ----- |
| 0 | [module-00-python-fundamentals](module-00-python-fundamentals/) | Data structures, modules, CLI, logging, async, HTTP |
| 1 | [module-01-working-with-the-llm](module-01-working-with-the-llm/) | LLM APIs, chat integration, streaming, prompting patterns |
| 2 | [module-02-agent-core](module-02-agent-core/) | Message format, tool registry, safety rails, eval harness |
| 3 | [module-03-mcp-server](module-03-mcp-server/) | MCP concepts, build a server, practical tools, auth |
| 4 | [module-04-genai-strategies](module-04-genai-strategies/) | Structured outputs, vision, multimodal API — the Day 1 closer |

### Day 2 — Knowledge + retrieval

| Block | Module | Topic |
| ----- | ------ | ----- |
| 5 | [module-05-rag-fundamentals](module-05-rag-fundamentals/) | Chunking, embeddings, vector stores, retrieval, evaluation |
| 6 | [module-06-multi-agent](module-06-multi-agent/) | Roles, coordination patterns, shared context |
| 7 | [module-07-agent-memory](module-07-agent-memory/) | Short/long-term memory, summarisation, ReAct, plan-and-execute |
| 8 | [module-08-structured-facts](module-08-structured-facts/) | Structured outputs, fact extraction, knowledge graphs, grounded QA |

### Day 3 — Ship it

| Block | Module | Topic |
| ----- | ------ | ----- |
| 9 | [module-09-adaptive-retrieval](module-09-adaptive-retrieval/) | Retrieval routing, self-critique, query decomposition, multi-source QA |
| 10 | [module-10-production](module-10-production/) | Tracing, reliability, cost controls, deployment |
| 11 | [module-11-langchain](module-11-langchain/) | Chains, agents, tools, RAG — framework-powered AI |
| 12 | [module-12-capstone](module-12-capstone/) | Full agentic app: chatbot + RAG + MCP + multi-agent |

## Course outline

All **exercises** run in **Python** and are checked with **pytest** (`start.py` / `test_start.py`). **Demos** are plain `python …` scripts. Optional **slides** under each module's `slides/` folder are separate Vite + React apps for teaching only.

### Module 0 — [Python Fundamentals](module-00-python-fundamentals/)

**Topics:** Data structures (lists, dicts, sets, tuples), modules/packages, CLI args, logging, dataclasses, Protocols, asyncio (tasks, queues, timeouts, cancellation), HTTP basics with FastAPI and httpx.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Dataclass filtering | [`exercises/01-dataclass-filtering`](module-00-python-fundamentals/exercises/01-dataclass-filtering/) | Parse/filter/transform crew JSON with dataclasses, CLI args |
| Async queue processing | [`exercises/02-async-queue-processing`](module-00-python-fundamentals/exercises/02-async-queue-processing/) | Async queue processing ship sensor data with timeouts |
| FastAPI CRUD | [`exercises/03-fastapi-crud`](module-00-python-fundamentals/exercises/03-fastapi-crud/) | FastAPI CRUD for missions with httpx test client |

### Module 1 — [Working with the LLM](module-01-working-with-the-llm/)

**Topics:** LLM API integration (chat completions, message roles, parameters), streaming responses, prompting patterns (structured outputs, grounding, tool calling), building a simple chat interface, session storage.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| First chat | [`exercises/01-first-chat`](module-01-working-with-the-llm/exercises/01-first-chat/) | First LLM API call + interactive console chat |
| Streaming | [`exercises/02-streaming`](module-01-working-with-the-llm/exercises/02-streaming/) | Stream responses token by token |
| Chat app | [`exercises/03-chat-app`](module-01-working-with-the-llm/exercises/03-chat-app/) | Slash commands + file persistence |

### Module 2 — [Agent Core](module-02-agent-core/)

**Topics:** Message format + state, tool registry pattern (schema, validation, routing, error handling), safety rails (allowlists, rate limits, redaction, audit logs), evaluation harness (golden tests, replay, deterministic mocks).

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Tool-calling agent | [`exercises/01-tool-calling-agent`](module-02-agent-core/exercises/01-tool-calling-agent/) | Build a tool-calling agent with real OpenAI API calls |
| Tool registry | [`exercises/02-tool-registry`](module-02-agent-core/exercises/02-tool-registry/) | Decorator-based registry plugged into the agent loop |
| Guarded agent | [`exercises/03-guarded-agent`](module-02-agent-core/exercises/03-guarded-agent/) | AllowList + RateLimiter + audit log wrapping the agent |

### Module 3 — [MCP Server](module-03-mcp-server/)

**Topics:** MCP concepts (tool discovery, schemas, calling conventions), building a minimal MCP server, practical tools (sensor reads, crew lookup, log search), auth + permissions, observability, building an MCP client.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Hello MCP | [`exercises/01-hello-mcp`](module-03-mcp-server/exercises/01-hello-mcp/) | Minimal MCP server exposing one tool |
| MCP tools | [`exercises/02-mcp-tools`](module-03-mcp-server/exercises/02-mcp-tools/) | Three ship-system tools: sensor read, crew lookup, log query |
| Auth + observability | [`exercises/03-auth-observability`](module-03-mcp-server/exercises/03-auth-observability/) | Per-tool auth scopes and structured logging |
| MCP client | [`exercises/04-mcp-client`](module-03-mcp-server/exercises/04-mcp-client/) | Build an MCP client: discover tools, validate args, handle errors |

### Module 4 — [GenAI Strategies](module-04-genai-strategies/)

**Topics:** Structured outputs (Pydantic, `response_format`), prompt engineering, model selection trade-offs, multimodal (vision via GPT-4o, audio via Whisper), building a FastAPI multimodal API.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Structured outputs | [`exercises/01-structured-outputs`](module-04-genai-strategies/exercises/01-structured-outputs/) | Pydantic model + `response_format` for reliable JSON |
| Vision | [`exercises/02-vision`](module-04-genai-strategies/exercises/02-vision/) | Send images to GPT-4o, get structured analysis |
| Multimodal API | [`exercises/03-multimodal-api`](module-04-genai-strategies/exercises/03-multimodal-api/) | FastAPI app with /chat, /vision, /transcribe endpoints |

### Module 5 — [RAG Fundamentals](module-05-rag-fundamentals/)

**Topics:** Chunking strategies (size, overlap, structure-aware), embeddings and vector stores (local and managed), retrieval (dense, sparse, hybrid, reranking), grounded prompting with citations, RAG evaluation.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Document chunker | [`exercises/01-document-chunker`](module-05-rag-fundamentals/exercises/01-document-chunker/) | Chunk ship logs into overlapping windows for indexing |
| Vector search | [`exercises/02-vector-search`](module-05-rag-fundamentals/exercises/02-vector-search/) | Embed and search the mission archives |
| RAG pipeline | [`exercises/03-rag-pipeline`](module-05-rag-fundamentals/exercises/03-rag-pipeline/) | End-to-end RAG with citation linking back to sources |

### Module 6 — [Multi-Agent Systems](module-06-multi-agent/)

**Topics:** When multi-agent helps vs hurts, agent roles (router, researcher, coder, critic), coordination patterns (supervisor, swarm, debate, blackboard), shared context and tools, consensus and conflict resolution.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Router agent | [`exercises/01-router-agent`](module-06-multi-agent/exercises/01-router-agent/) | Route queries to navigation, engineering, or science specialists |
| Supervisor-critic | [`exercises/02-supervisor-critic`](module-06-multi-agent/exercises/02-supervisor-critic/) | Supervisor coordinates researcher + critic for mission briefings |
| Consensus | [`exercises/03-consensus`](module-06-multi-agent/exercises/03-consensus/) | Multiple agents propose answers; vote on the best response |

### Module 7 — [Agent Memory + Workflows](module-07-agent-memory/)

**Topics:** Short-term session memory vs long-term profile, summarisation for context limits, decay and "do not remember" controls, workflow patterns (ReAct, plan-and-execute, tool routing).

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Memory store | [`exercises/01-memory-store`](module-07-agent-memory/exercises/01-memory-store/) | Short-term buffer and long-term memory with decay |
| Conversation summary | [`exercises/02-conversation-summary`](module-07-agent-memory/exercises/02-conversation-summary/) | Summarise long conversations to fit a token budget |
| ReAct loop | [`exercises/03-react-loop`](module-07-agent-memory/exercises/03-react-loop/) | Implement ReAct: Reason, Act, Observe |

### Module 8 — [Structured Facts](module-08-structured-facts/)

**Topics:** Structured outputs (Pydantic, JSON Schema), fact extraction pipelines with provenance and confidence, knowledge graph construction (entities, relationships), grounded QA with citations.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Fact extractor | [`exercises/01-fact-extractor`](module-08-structured-facts/exercises/01-fact-extractor/) | Extract structured facts from ship logs using Pydantic schemas |
| Knowledge graph | [`exercises/02-knowledge-graph`](module-08-structured-facts/exercises/02-knowledge-graph/) | Build a graph from entities and query for relationships |
| Grounded QA | [`exercises/03-grounded-qa`](module-08-structured-facts/exercises/03-grounded-qa/) | Answer questions with source citations and confidence scores |

### Module 9 — [Adaptive Retrieval](module-09-adaptive-retrieval/)

**Topics:** Retrieval routing (vector, graph, keyword), query decomposition, self-critique loops (corrective RAG), multi-source orchestration with merge and ranking.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Retrieval router | [`exercises/01-retrieval-router`](module-09-adaptive-retrieval/exercises/01-retrieval-router/) | Route queries to vector, graph, or keyword search |
| Self-critique | [`exercises/02-self-critique`](module-09-adaptive-retrieval/exercises/02-self-critique/) | Evaluate retrieval quality and refine queries |
| Multi-source QA | [`exercises/03-multi-source-qa`](module-09-adaptive-retrieval/exercises/03-multi-source-qa/) | Fan out to multiple backends, merge, rank, answer with citations |

### Module 10 — [Production & Deployment](module-10-production/)

**Topics:** Structured tracing and logging, reliability (retries, circuit breakers, fallbacks), cost controls (budgets, batching, model tiering), environment config, secrets, containers, CI/CD.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Trace middleware | [`exercises/01-trace-middleware`](module-10-production/exercises/01-trace-middleware/) | Add trace IDs and timing to every tool call |
| Batch pipeline | [`exercises/02-batch-pipeline`](module-10-production/exercises/02-batch-pipeline/) | Batch LLM requests with retry and fallback model |
| Cost tracker | [`exercises/03-cost-tracker`](module-10-production/exercises/03-cost-tracker/) | Per-session token and cost budget enforcement |
| Deploy container | [`exercises/04-deploy-container`](module-10-production/exercises/04-deploy-container/) | Health-check app, env config, Dockerfile validation |

### Module 11 — [LangChain with Python](module-11-langchain/)

**Topics:** LangChain vs hand-rolled (chains, agents, tools, memory, output parsers), prompt templates and LCEL, rewriting agent loops with LangChain, connecting to MCP and RAG pipelines.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Chain basics | [`exercises/01-chain-basics`](module-11-langchain/exercises/01-chain-basics/) | Prompt template + chain for crew report classification |
| Tool agent | [`exercises/02-tool-agent`](module-11-langchain/exercises/02-tool-agent/) | Wrap ship tools as LangChain tools, run via AgentExecutor |
| RAG chain | [`exercises/03-rag-chain`](module-11-langchain/exercises/03-rag-chain/) | RetrievalQA chain over the Pathfinder knowledge base |

### Module 12 — [Capstone Project](module-12-capstone/)

**Topics:** Full agentic application integrating chat, RAG, MCP tools, and multi-agent coordination. Demo scenarios, integration tests, extension documentation.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Capstone app | [`exercises/01-capstone-app`](module-12-capstone/exercises/01-capstone-app/) | Integrated chat + RAG + MCP + multi-agent app |
| Test and extend | [`exercises/02-test-and-extend`](module-12-capstone/exercises/02-test-and-extend/) | Integration tests and extension documentation |

## Running tests

```bash
# All exercises
pytest

# One module
pytest module-01-working-with-the-llm/

# One exercise
pytest module-00-python-fundamentals/exercises/01-dataclass-filtering/test_start.py

# With verbose output
pytest -v module-02-agent-core/
```

## License

Copyright (c) 2026 Nicholas Johnson. **All rights reserved.** This material is not licensed for use, copying, or distribution by others. See [LICENSE](LICENSE).
