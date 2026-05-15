# AI Engineering with Python — Course Outline

Build production-grade AI systems — agents, tools, RAG pipelines, and multi-agent workflows — in Python.

---

## Day 1 — Build a working chatbot

### Module 0 — Python Fundamentals

- Work fluently with Python data structures, modules/packages, CLI args, and logging.
- Model domain objects with dataclasses and define contracts with Protocols.
- Write async code: asyncio tasks, queues, timeouts, and cancellation.
- Build and test a basic HTTP API with FastAPI and httpx.

### Module 1 — Working with the LLM

- Call the LLM chat-completion API directly — message roles, parameters, streaming.
- Build a CLI chat loop with conversation history and a FastAPI streaming endpoint with SSE.
- Implement session storage: in-memory first, then file-based.
- Apply prompting patterns that hold up in production (structured outputs, grounding).

### Module 2 — Tool Calling

- Understand the message format that drives an agent (system, user, assistant, tool messages).
- Build a tool-calling loop: schema in, action out, result back, repeat.
- Implement a tool registry with schema validation, routing, and error handling.
- Add safety rails (allowlists, rate limits, redaction) and an evaluation harness with golden tests.

### Module 3 — GenAI Strategies

- Apply prompt engineering: system prompts, few-shot examples, structured outputs, and grounding.
- Work with multimodal inputs and outputs: vision/image analysis, speech-to-text, text-to-speech.
- Add guardrails: model selection, token budgeting, content filters, and confidence thresholds.

---

## Day 2 — MCP + knowledge

### Module 4 — MCP Server

- Understand MCP concepts: tool discovery, schemas, calling conventions.
- Build a minimal MCP server in Python, then add practical tools.
- Implement real-world tools: data lookups, queries, sensor reads.
- Add per-tool auth scopes and structured logging for observability.

### Module 5 — RAG Fundamentals

- Design chunking strategies (size, overlap, structure-aware splits) for long documents.
- Produce embeddings, store them in a vector index, and query effectively.
- Apply retrieval strategies: hybrid search, metadata filters, reranking, and grounded answers with citations.
- Run basic RAG evaluation: recall/precision on retrieval and adversarial queries.

### Module 6 — Multi-Agent Systems

- Decide when multi-agent designs are worth the latency and operational complexity.
- Model roles (router, researcher, coder, critic) and coordination patterns (supervisor, swarm, debate).
- Share context and tools safely across agents and apply conflict resolution / consensus strategies.

### Module 7 — Agent Memory + Workflows

- Implement short-term memory (conversation/session) separate from long-term profile or notes.
- Apply summarisation to fit context limits; model decay and explicit "do not remember" controls.
- Compare workflow patterns: ReAct, plan-and-execute, and tool routing for multi-step tasks.

---

## Day 3 — Structured knowledge + ship it

### Module 8 — Structured Facts

- Use structured outputs (Pydantic models, JSON Schema) to get reliable, typed data from an LLM.
- Build a fact extraction pipeline that decomposes text into individual claims with provenance.
- Construct a knowledge graph from extracted entities and relationships.
- Implement grounded QA that answers questions from the graph and cites source documents.

### Module 9 — Adaptive Retrieval

- Build a retrieval router that selects the right source (vector store, knowledge graph, keyword search) based on query type.
- Implement query decomposition — breaking complex questions into focused sub-queries.
- Add a self-critique loop (corrective RAG) that evaluates retrieved documents and re-retrieves when quality is low.
- Orchestrate multi-source retrieval — merging results from different backends with relevance scoring.

### Module 10 — Production Concerns

- Add tracing and structured logging so every tool call is attributable and debuggable.
- Define metrics and timelines that surface latency, errors, and dependency health.
- Implement reliability (retries, timeouts, circuit breakers, fallbacks) and cost controls (caching, batching, token budgets).
- Outline deployment: containers, running MCP alongside HTTP APIs, and config per environment.

### Module 11 — LangChain with Python

- Understand what LangChain provides vs building from scratch: chains, agents, tools, memory, and output parsers.
- Rewrite a hand-rolled agent loop using LangChain components and compare the trade-offs.
- Connect LangChain to an MCP server and RAG pipeline built in earlier modules.

### Module 12 — Capstone Project

- Build a full agentic application: chat UI or CLI, RAG, MCP tools, and a coordinated multi-agent path for complex questions.
- Write demo scenarios and integration tests that guard against regressions.
- Document extension points for adding tools, data sources, and policies.
