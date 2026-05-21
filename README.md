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

- **Python** 3.12 or newer — check with `python3 --version` or `py --version`
- **pip** (bundled with Python — used inside a virtual environment)
- **Node.js** v20+ and **pnpm** v10+ (for slides only) — `corepack enable && corepack prepare pnpm@latest --activate`
- A code editor (VS Code / Cursor recommended)
- An OpenAI API key (or compatible provider) in your environment

## Setup

### Python environment

Create a virtual environment and install dependencies:

```bash
cd ai-python-course

# Create a virtual environment (use whichever python command gives you 3.12+)
python3 -m venv .venv        # or: py -m venv .venv

# Activate it
source .venv/bin/activate    # macOS / Linux
# .venv\Scripts\activate     # Windows

# Install dependencies
pip install -e .

# With optional extras (pick what you need)
pip install -e ".[dev]"                        # pytest + ruff
pip install -e ".[rag]"                        # chromadb, sentence-transformers
pip install -e ".[langchain]"                  # langchain, langgraph
pip install -e ".[local-ml]"                     # torch, transformers (CPU training)
pip install -e ".[dev,rag,langchain,structured,local-ml]"  # everything
```

> **Tip:** If `python3 --version` shows an old version but `py --version` shows 3.12+, use `py` instead. On macOS with Homebrew Python you **must** use a virtual environment — pip will refuse to install system-wide.

You need to activate the venv (`source .venv/bin/activate`) each time you open a new terminal.

### Slides dependencies (pnpm monorepo)

```bash
pnpm install
```

### Running tests

```bash
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
| 2 | [module-02-tool-calling](module-02-tool-calling/) | Message format, tool registry, safety rails, eval harness |
| 3 | [module-03-mcp-server](module-03-mcp-server/) | MCP concepts, build a server, practical tools, auth |
| 4 | [module-04-genai-strategies](module-04-genai-strategies/) | Research Assistant app: streaming chat, MCP tools, multimodal — the Day 1 closer |

### Day 2 — Knowledge + retrieval

| Block | Module | Topic |
| ----- | ------ | ----- |
| 5 | [module-05-rag-fundamentals](module-05-rag-fundamentals/) | Chunking, embeddings, vector stores, retrieval, evaluation |
| 6 | [module-06-structured-facts](module-06-structured-facts/) | Structured outputs, fact extraction, knowledge graphs, grounded QA |
| 7 | [module-07-agent-memory](module-07-agent-memory/) | Short/long-term memory, summarisation, decay controls |
| 8 | [module-08-structured-workflows](module-08-structured-workflows/) | ReAct, plan-and-execute, tool routing — the Day 2 closer |

### Day 3 — Ship it

| Block | Module | Topic |
| ----- | ------ | ----- |
| 9 | [module-09-multi-agent](module-09-multi-agent/) | Roles, coordination patterns, shared context |
| 10 | [module-10-langchain](module-10-langchain/) | Chains, agents, tools, RAG — framework-powered AI |
| 11 | [module-11-edge-topics](module-11-edge-topics/) | Hybrid search, re-ranking, HyDE, agentic RAG, eval, guardrails, and more |
| 12 | [module-12-productionisation](module-12-productionisation/) | Production hardening + capstone apps: tracing, reliability, cost controls, deployment |

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

### Module 2 — [Tool Calling](module-02-tool-calling/)

**Topics:** Message format + state, tool registry pattern (schema, validation, routing, error handling), safety rails (allowlists, rate limits, redaction, audit logs), evaluation harness (golden tests, replay, deterministic mocks).

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Tool-calling agent | [`exercises/01-tool-calling-agent`](module-02-tool-calling/exercises/01-tool-calling-agent/) | Build a tool-calling agent with real OpenAI API calls |
| Tool registry | [`exercises/02-tool-registry`](module-02-tool-calling/exercises/02-tool-registry/) | Decorator-based registry plugged into the agent loop |
| Guarded agent | [`exercises/03-guarded-agent`](module-02-tool-calling/exercises/03-guarded-agent/) | AllowList + RateLimiter + audit log wrapping the agent |

### Module 3 — [MCP Server](module-03-mcp-server/)

**Topics:** MCP concepts (tool discovery, schemas, calling conventions), building FastMCP servers, connecting to an agent via MCP stdio, dynamic tool discovery, real-world tools (web fetch, file I/O).

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| MCP agent | [`exercises/01-mcp-agent`](module-03-mcp-server/exercises/01-mcp-agent/) | FastMCP server + console agent connected via MCP stdio |
| Data tools | [`exercises/02-data-tools`](module-03-mcp-server/exercises/02-data-tools/) | Server reading crew, logs, sensors, missions from JSON data |
| Live tools | [`exercises/03-live-tools`](module-03-mcp-server/exercises/03-live-tools/) | Server with web fetch and note file management |

### Module 4 — [GenAI Strategies](module-04-genai-strategies/)

**Topics:** Prompt engineering, structured outputs, model selection trade-offs, multimodal (vision via GPT-4o, audio via Whisper), FastAPI with SSE streaming, MCP tool integration in a web API. Delegates build a **Research Assistant** web app -- the Day 1 closer.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Chat API | [`exercises/01-chat-api`](module-04-genai-strategies/exercises/01-chat-api/) | FastAPI backend with SSE streaming chat |
| Tool chat | [`exercises/02-tool-chat`](module-04-genai-strategies/exercises/02-tool-chat/) | MCP server with web fetch + notes, tool-calling loop in the API |
| Multimodal | [`exercises/03-multimodal`](module-04-genai-strategies/exercises/03-multimodal/) | Add /vision (GPT-4o) and /transcribe (Whisper) endpoints |

### Module 5 — [RAG Fundamentals](module-05-rag-fundamentals/)

**Topics:** Chunking strategies (size, overlap, structure-aware), embeddings and vector stores (local and managed), retrieval (dense, sparse, hybrid, reranking), grounded prompting with citations, RAG evaluation.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Build the index | [`exercises/01-build-index`](module-05-rag-fundamentals/exercises/01-build-index/) | Chunk ship logs, embed with OpenAI, store in ChromaDB, interactive search |
| RAG chat | [`exercises/02-rag-chat`](module-05-rag-fundamentals/exercises/02-rag-chat/) | Grounded chat agent with source citations and /norag comparison |
| RAG MCP server | [`exercises/03-rag-mcp-server`](module-05-rag-fundamentals/exercises/03-rag-mcp-server/) | Wrap RAG as MCP server, connect to a tool-calling agent |

### Module 6 — [Structured Facts](module-06-structured-facts/)

**Topics:** Structured outputs (Pydantic, JSON Schema), fact extraction pipelines with provenance and confidence, knowledge graph construction (entities, relationships), grounded QA with citations.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Fact extractor | [`exercises/01-fact-extractor`](module-06-structured-facts/exercises/01-fact-extractor/) | Extract structured facts with OpenAI + Pydantic, interactive REPL |
| Knowledge graph | [`exercises/02-knowledge-graph`](module-06-structured-facts/exercises/02-knowledge-graph/) | Build a networkx graph from facts, query entities, find paths |
| Grounded QA | [`exercises/03-grounded-qa`](module-06-structured-facts/exercises/03-grounded-qa/) | Answer questions grounded in graph evidence with [Fact N] citations |

### Module 7 — [Agent Memory](module-07-agent-memory/)

**Topics:** Short-term session memory vs long-term profile, summarisation for context limits, decay and "do not remember" controls.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Memory store | [`exercises/01-memory-store`](module-07-agent-memory/exercises/01-memory-store/) | Short-term buffer and long-term memory with decay |
| Conversation summary | [`exercises/02-conversation-summary`](module-07-agent-memory/exercises/02-conversation-summary/) | Summarise long conversations to fit a token budget |
| Memory MCP server | [`exercises/03-memory-server`](module-07-agent-memory/exercises/03-memory-server/) | Expose memory as an MCP server for agent integration |

### Module 8 — [Structured Workflows](module-08-structured-workflows/)

**Topics:** Workflow patterns (ReAct, plan-and-execute, tool routing), chaining reasoning steps, dynamic replanning, structured execution traces.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| ReAct agent | [`exercises/01-react-agent`](module-08-structured-workflows/exercises/01-react-agent/) | Implement ReAct: Reason, Act, Observe |
| Plan-and-execute | [`exercises/02-plan-and-execute`](module-08-structured-workflows/exercises/02-plan-and-execute/) | Decompose a goal into steps, execute, and replan |
| Holiday planner | [`exercises/03-holiday-planner`](module-08-structured-workflows/exercises/03-holiday-planner/) | Multi-step workflow combining tools to plan a trip |

### Module 9 — [Multi-Agent Systems](module-09-multi-agent/)

**Topics:** When multi-agent helps vs hurts, agent roles (router, researcher, coder, critic), coordination patterns (supervisor, swarm, debate, blackboard), shared context and tools, consensus and conflict resolution.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Router agent | [`exercises/01-router-agent`](module-09-multi-agent/exercises/01-router-agent/) | Route queries to medical, tactical, or comms specialists |
| Supervisor-critic | [`exercises/02-supervisor-critic`](module-09-multi-agent/exercises/02-supervisor-critic/) | Supervisor orchestrates specialists + critic with a revision loop |
| Consensus | [`exercises/03-consensus`](module-09-multi-agent/exercises/03-consensus/) | Debate pattern, judge synthesis, and consensus voting |
| Swarm tools | [`exercises/04-swarm-tools`](module-09-multi-agent/exercises/04-swarm-tools/) | Scoped tools and peer-to-peer handoffs between agents |

### Module 10 — [LangChain with Python](module-10-langchain/)

**Topics:** LangChain vs hand-rolled (chains, agents, tools, memory, output parsers), prompt templates and LCEL, rewriting agent loops with LangChain, connecting to MCP and RAG pipelines.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Chain basics | [`exercises/01-chain-basics`](module-10-langchain/exercises/01-chain-basics/) | Prompt template + chain for crew report classification |
| Tool agent | [`exercises/02-tool-agent`](module-10-langchain/exercises/02-tool-agent/) | Wrap ship tools as LangChain tools, run via AgentExecutor |
| RAG chain | [`exercises/03-rag-chain`](module-10-langchain/exercises/03-rag-chain/) | RetrievalQA chain over the Pathfinder knowledge base |
| LangServe API | [`exercises/04-langserve-api`](module-10-langchain/exercises/04-langserve-api/) | Expose the Horizon classifier as a FastAPI service via LangServe |

### Module 11 — [Edge Topics](module-11-edge-topics/)

**Topics:** Advanced retrieval patterns (hybrid search, re-ranking, HyDE), agentic RAG, citation verification, web search backends, text-to-SQL, LLM evaluation, fine-tuning data pipelines, guardrails, semantic caching, multimodal RAG, contextual chunking. Pick-and-choose — delegates work on topics that interest them most.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Hybrid search | [`exercises/01-hybrid-search`](module-11-edge-topics/exercises/01-hybrid-search/) | Combine dense and sparse retrieval |
| Reranking | [`exercises/02-reranking`](module-11-edge-topics/exercises/02-reranking/) | Re-rank retrieved results for relevance |
| HyDE | [`exercises/03-hyde`](module-11-edge-topics/exercises/03-hyde/) | Hypothetical Document Embeddings for better retrieval |
| Agentic RAG | [`exercises/04-agentic-rag`](module-11-edge-topics/exercises/04-agentic-rag/) | Agent-driven retrieval with self-critique |
| Citation verification | [`exercises/05-citation-verification`](module-11-edge-topics/exercises/05-citation-verification/) | Verify and ground citations in source documents |
| Web search backend | [`exercises/06-web-search-backend`](module-11-edge-topics/exercises/06-web-search-backend/) | Integrate web search as a retrieval source |
| Text-to-SQL | [`exercises/07-text-to-sql`](module-11-edge-topics/exercises/07-text-to-sql/) | Natural language to SQL query generation |
| LLM eval | [`exercises/08-llm-eval`](module-11-edge-topics/exercises/08-llm-eval/) | Evaluate LLM outputs with automated metrics |
| Fine-tuning data | [`exercises/09-fine-tuning-data`](module-11-edge-topics/exercises/09-fine-tuning-data/) | Build datasets for fine-tuning |
| Guardrails | [`exercises/10-guardrails`](module-11-edge-topics/exercises/10-guardrails/) | Input/output validation and safety filters |
| Semantic cache | [`exercises/11-semantic-cache`](module-11-edge-topics/exercises/11-semantic-cache/) | Cache LLM responses by semantic similarity |
| Multimodal RAG | [`exercises/12-multimodal-rag`](module-11-edge-topics/exercises/12-multimodal-rag/) | RAG with images and text |
| Contextual chunking | [`exercises/13-contextual-chunking`](module-11-edge-topics/exercises/13-contextual-chunking/) | Context-aware document chunking strategies |

### Module 12 — [Productionisation](module-12-productionisation/)

**Topics:** Production hardening (tracing, retries, circuit breakers, cost controls, deployment) plus capstone apps. Choose one full-stack app and build a production-ready FastAPI backend for a provided frontend.

| Exercise | Folder | What you practise |
| -------- | ------ | ----------------- |
| Recipe Finder | [`exercises/01-recipe-finder`](module-12-productionisation/exercises/01-recipe-finder/) | RAG, hybrid search, reranking, multimodal vision, allergen guardrails |
| Movie Night | [`exercises/02-movie-night`](module-12-productionisation/exercises/02-movie-night/) | RAG, hybrid search, text-to-SQL, structured output, charts |
| Travel Planner | [`exercises/03-travel-planner`](module-12-productionisation/exercises/03-travel-planner/) | Agentic RAG, tool calling, structured itineraries, web fallback |
| Personal Assistant | [`exercises/04-personal-assistant`](module-12-productionisation/exercises/04-personal-assistant/) | Chat + tools + MCP, RAG over notes, calendar management, cost controls |

## License

Copyright (c) 2026 Nicholas Johnson. **All rights reserved.** This material is not licensed for use, copying, or distribution by others. See [LICENSE](LICENSE).
