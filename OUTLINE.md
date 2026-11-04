# AI Engineering with Python — Course Outline

Build production-grade AI systems — agents, tools, RAG pipelines, and multi-agent workflows — in Python.

Modules 1–13 run across three days. Module 0 is prework, covered only if the group needs it. For the delivery schedule and per-module demo/exercise breakdown, see [MSCI-three-day-outline.md](MSCI-three-day-outline.md).

---

## Module 0 — Python Fundamentals *(prework)*

- Work fluently with Python data structures: lists, dicts, sets, tuples.
- Organise code with modules/packages, CLI args (`argparse`), and logging.
- Model domain objects with dataclasses and define contracts with `Protocol`.
- Write async code: `asyncio` tasks, queues, timeouts, and cancellation.
- Build and test a basic HTTP API with FastAPI and httpx.

---

## Day 1 — Build a working agent

### Module 1 — Working with the LLM

- Call the LLM directly with OpenAI's Responses API (instructions, input, message roles, the response object).
- Recognise the older Chat Completions API — still supported and common in existing code, but being phased out.
- Build a CLI chat loop with conversation history.
- Stream responses token by token for real-time output.
- Apply prompting patterns that hold up in production (personas, format constraints, guardrails, few-shot examples).

### Module 2 — Tool Calling

- Understand the conversation items that drive an agent (system, user and assistant messages; function calls and their outputs).
- Build a tool-calling loop with real OpenAI API calls: schema in, action out, result back, repeat.
- Implement a tool registry with decorator registration, routing, and error handling.
- Add safety rails: allowlists, rate limits, audit logs.

### Module 3 — MCP Server

- Understand the Model Context Protocol: tool discovery, schemas, calling conventions.
- Build MCP servers with `MCPServer` and practical tools: data queries, web fetch, file I/O.
- Connect an MCP server to a real agent via `mcp.client.stdio`.
- Convert MCP tool schemas to OpenAI tool-calling format for dynamic discovery.

### Module 4 — GenAI Strategies *(Day 1 closer)*

- Build a FastAPI app with SSE streaming chat, tool integration, and multimodal endpoints.
- Connect an MCP server to a web API for real-time tool use.
- Reason about model selection trade-offs: quality, cost, latency.
- Count tokens and enforce budgets before calling the model.
- Work with multimodal inputs: vision/image analysis and speech-to-text.
- Apply guardrails: schema validation, content filters, and confidence thresholds.

---

## Day 2 — Knowledge + retrieval

### Module 5 — RAG Fundamentals

- Split documents into chunks (fixed-size, sentence-aware, structure-aware, overlap) and synthetic units (extracted facts, generated FAQs).
- Generate embeddings with `text-embedding-3-small` and store them in ChromaDB.
- Expand queries at search time with query expansion and HyDE.
- Build grounded prompts with source citations.
- Wrap a RAG pipeline as MCP tools any agent can call.

### Module 6 — Structured Facts

- Use Pydantic models to define structured output schemas.
- Build a fact extraction pipeline: claims, provenance, and confidence scores.
- Construct a knowledge graph: entities, relationships, and traversal with `networkx`.
- Implement grounded QA from graphs with citations.
- Expose the graph as an MCP server and let an agent loop choose the traversal.

### Module 7 — Agent Memory and Context Engineering

- Account for a context window as a budget and know where the tokens actually go.
- Write memories worth keeping, and supersede facts instead of stacking contradictions.
- Select memories by semantic recall, scored on relevance, recency, and importance.
- Compact a long conversation without losing the decisions and open tasks inside it.
- Expose memory and compaction as MCP tools so any agent can use them.

### Module 8 — Structured Workflows *(Day 2 closer)*

- Place a task on the control-flow spectrum: fixed chain, router, plan-and-execute, ReAct.
- Build a ReAct loop whose reasoning is visible, with a step budget, repeat detection, and a forced finish.
- Build plan-and-execute with re-planning on failure.
- Run independent plan steps concurrently with a `depends_on` graph.
- Pause a plan for human approval, checkpoint it to disk, and resume without repeating work.

---

## Day 3 — Ship it

### Module 9 — Multi-Agent Systems

- Know when to use multi-agent systems (and when a single agent is better).
- Define agent roles: router, researcher, critic, supervisor, executor.
- Implement coordination patterns: supervisor, swarm, debate, blackboard, task queue.
- Share context and tools between agents safely.
- Build conflict resolution and consensus mechanisms.
- Spawn subagents on demand, run them in parallel, and reconcile their reports.

### Module 10 — LangChain with Python

- Build LCEL chains: prompt templates, the pipe operator, and structured output with Pydantic.
- Wrap functions as LangChain tools and run them with `create_agent` (LangChain 1.x), adding middleware and memory.
- Construct a RAG chain with a LangChain retriever and ChromaDB, then turn retrieval into an agent tool (agentic RAG).
- Serve an LCEL chain as a REST API with FastAPI using the Runnable `ainvoke` / `astream` methods.
- Know when to use LangChain and when to stay hand-rolled.

### Module 11 — Evals

- Catch agent regressions with golden tests: a frozen reference, exact-match tool calls, and a judged answer.
- Score retrieval with recall@k, precision@k, and MRR against a labelled query set.
- Grade answers with an LLM-as-judge on correctness, completeness, and relevance.
- Measure faithfulness: every claim in an answer must be grounded in retrieved context.
- Compare two configs on a scorecard and fail a release that drops below a threshold.

### Module 12 — Productionisation

- Implement structured tracing with trace IDs and spans.
- Apply reliability patterns: retries with backoff, timeouts, circuit breakers, fallbacks.
- Enforce cost controls: token budgets, model tiering, caching.
- Deploy with environment config, secrets management, and health checks.
- Pick one capstone (exercises 04–07) and build its FastAPI backend. The frontend is provided.

| App | Folder | Techniques practised |
| --- | ------ | -------------------- |
| Recipe Finder | `exercises/04-recipe-finder` | RAG, hybrid search, reranking, multimodal vision, allergen guardrails |
| Movie Night | `exercises/05-movie-night` | RAG, hybrid search, text-to-SQL, structured output |
| Travel Planner | `exercises/06-travel-planner` | Agentic RAG, tool calling, structured itineraries, web fallback |
| Personal Assistant | `exercises/07-personal-assistant` | Chat + tools + MCP, RAG over notes, calendar, cost controls |

### Module 13 — Edge Topics *(pick and choose)*

Independent advanced techniques; exercise numbers match topic numbers.

- Retrieval quality: hybrid search (RRF), re-ranking, HyDE, contextual chunking.
- Agentic and trust: agentic RAG, citation verification, web search backend.
- Data: text-to-SQL, fine-tuning data prep (DPO + LoRA).
- Production UX: advanced guardrails, semantic caching, multimodal RAG.
- Local ML on a laptop CPU: train a small model, run a Hugging Face model.
- Concepts only: test-time compute scaling, speculative decoding, GraphRAG, mixture of experts.

