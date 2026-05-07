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
pytest module-01-python-fundamentals/exercises/01-crew-manifest/test_start.py
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
| Crew manifest | [`exercises/01-crew-manifest`](module-01-python-fundamentals/exercises/01-crew-manifest/) | Parse/filter/transform crew JSON with dataclasses, CLI args |
| Async sensor relay | [`exercises/02-async-sensor-relay`](module-01-python-fundamentals/exercises/02-async-sensor-relay/) | Async queue processing ship sensor data with timeouts |
| Mission API | [`exercises/03-mission-api`](module-01-python-fundamentals/exercises/03-mission-api/) | FastAPI CRUD for missions with httpx test client |

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

### Module 5 — [MCP Server](module-05-mcp-server/)

**Topics:** MCP concepts (tool discovery, schemas, calling conventions), building a minimal MCP server, practical tools (filesystem, HTTP fetch, DB query, calculators), auth + permissions, observability, versioning.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Hello MCP | [`exercises/01-hello-mcp`](module-05-mcp-server/exercises/01-hello-mcp/) | Minimal MCP server exposing one tool |
| Ship tools | [`exercises/02-ship-tools`](module-05-mcp-server/exercises/02-ship-tools/) | Three ship-system tools: sensor read, crew lookup, log query |
| Auth + observability | [`exercises/03-auth-observability`](module-05-mcp-server/exercises/03-auth-observability/) | Per-tool auth scopes and structured logging |

### Modules 6–13

See each module's README for learning goals and exercise outlines.

## Running tests

```bash
# All exercises
pytest

# One module
pytest module-01-python-fundamentals/

# One exercise
pytest module-01-python-fundamentals/exercises/01-crew-manifest/test_start.py

# With verbose output
pytest -v module-02-agent-core/
```

## License

Copyright (c) 2026 Nicholas Johnson. **All rights reserved.** This material is not licensed for use, copying, or distribution by others. See [LICENSE](LICENSE).
