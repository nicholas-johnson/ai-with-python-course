# Instructor Guide

## Day 1 — Build a working agent

### Module 1 — Working with the LLM

**Talk about:**

- Chat-completion API: message roles (system/user/assistant), sending a list, getting a response
- The chat loop pattern: while-loop, append user input, call API, append response
- Why streaming matters: perceived latency, first token in 200ms vs 3s blank screen
- Streaming with the OpenAI SDK: `stream=True`, iterating over chunks, `delta.content`
- Prompt engineering: personas, format constraints, guardrails, few-shot examples

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-01-working-with-the-llm/demo/demo.py` | All-in-one walkthrough. Part 1: basic chat call, message list growing. Part 2: streaming tokens live. Part 3: same question through different system prompts (persona, bullets, JSON, guardrails, few-shot). |

**Exercises (chained — each builds on the previous):**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-first-chat` | First API call + console input loop. `python start.py` for interactive chat. |
| `exercises/02-streaming` | Streaming upgrade — tokens print as they arrive. Ships with ex01 solution. |
| `exercises/03-prompting` | Write system prompts for 6 challenges (persona, format, JSON, haiku, guardrails, few-shot). Ships with run_prompt() helper. |

---

### Module 2 — Tool Calling

**Talk about:**

- The 4th role: `tool` — model requests actions via tool_calls, you execute and feed results back
- The tool-calling loop: ask → tool? → execute → append result → ask again. Cap with max_steps.
- Tool registry: JSON Schema per tool, decorator registration, validate-then-call, list_tools() output
- Safety rails: allowlists, rate limits (sliding window), audit logging
- Golden-file evaluation (demo only): mock LLM, scripted responses, assert tools + answer

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-02-tool-calling/demo/demo.py` | All four topics in one interactive walkthrough — press Enter between sections. Part 1: live tool call tracing 4 message roles. Part 2: decorator registry, list/call/error handling. Part 3: allowlist, rate limiter, redaction, audit log. Part 4: mock LLM golden tests. |

**Exercises (chained — each builds on the previous):**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-tool-calling-agent` | Tool-calling agent with real OpenAI API calls. `python start.py` for interactive CLI chat. |
| `exercises/02-tool-registry` | ToolRegistry class with decorator registration, plugged into the agent loop from ex01. |
| `exercises/03-guarded-agent` | AllowList + RateLimiter + GuardedAgent wrapping the registry from ex02. Audit log printed after each answer. |

---

### Module 3 — MCP Server

**Talk about:**

- What MCP is: JSON-RPC between agent host and tool server, tools/list and tools/call
- FastMCP: decorator-based, auto-generates schemas from type hints
- Practical tools: sensor reads, crew lookups, log search
- Auth and scopes: per-tool access control, token-based scoping
- Structured logging: every tool call logged with timestamp, caller, args, result, duration
- Building a client: discover tools dynamically, validate args, handle errors

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-03-mcp-server/demo/demo.py` | All three topics in one interactive walkthrough. Part 1: MCP protocol as data — discovery, call, result. Part 2: FastMCP decorator pattern and auto-generated schemas. Part 3: live agent connecting to an MCP server, discovering tools, calling them via OpenAI. |

**Exercises (chained — each builds on the previous):**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-mcp-agent` | FastMCP server + console agent connected via MCP stdio. `python start.py` for interactive chat. |
| `exercises/02-data-tools` | Richer server reading crew, logs, sensors, missions from JSON files. Ships with ex01 agent. |
| `exercises/03-live-tools` | Server with web fetch (httpx) + note save/list/read. Ships with ex01 agent. The "it actually does stuff" moment. |

---

### Module 4 — GenAI Strategies

**Talk about:**

- Prompt engineering: be specific, system prompts as standing orders, few-shot examples (2-3 pairs)
- Structured outputs: `response_format={"type": "json_object"}`, Pydantic validation, schema in system prompt
- Model selection trade-offs: quality vs cost vs latency, tiered routing
- Token counting and budgets (lecture): tiktoken, truncate or summarise if over budget
- Multimodal: Vision API (base64 image in message, content parts), Whisper for audio transcription
- Guardrails (lecture): schema validation, content filter, confidence threshold — already practised in Module 2
- FastAPI + SSE streaming for real-time chat backends

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-04-genai-strategies/demo/demo.py` | All three topics in one interactive walkthrough. Part 1: vague vs specific prompts, response_format, few-shot classification. Part 2: same task on GPT-4o vs GPT-4o-mini — latency, tokens, quality. Part 3: Pydantic guardrails chain — schema validation, content filter, confidence gate with 4 test cases + live LLM. |

**Exercises (chained — delegates build a Research Assistant web app):**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-chat-api` | FastAPI backend with SSE streaming `/chat` and `/health`. Frontend chat panel lights up. |
| `exercises/02-tool-chat` | MCP server with web fetch + notes tools. Extend chat with tool-calling loop. Frontend shows tool activity. |
| `exercises/03-multimodal` | Add `/vision` (GPT-4o image analysis) and `/transcribe` (Whisper). Frontend image/audio uploads work. |

A Svelte + ShadCN + Tailwind frontend is provided in `frontend/`. Delegates focus on the FastAPI backend.

---

## Day 2 — Knowledge + retrieval

### Module 5 — RAG Fundamentals

**Talk about:**

- Chunking strategies: size, overlap, structure-aware splits
- Embeddings: text-embedding-3-small, what vectors represent, dimensionality
- Vector stores: ChromaDB locally, similarity search, metadata filters
- Retrieval strategies: dense, sparse, hybrid, reranking
- Grounded prompts: retrieved chunks inserted as context, citations
- RAG evaluation: recall, precision, faithfulness, adversarial queries

**Demo:**

Multi-step walkthrough using persistent ChromaDB (Docker). Run from `module-05-rag-fundamentals/demo/`:

| Step | Command | What it shows |
| ---- | ------- | ------------- |
| 1 | `docker compose up -d` | Start ChromaDB server (port 8100) |
| 2 | `python ingest.py` | Load ship logs, chunk, embed, store in ChromaDB |
| 3 | `python -m mcp dev server.py` | (Optional) MCP Inspector — call RAG tools in browser |
| 4 | `python agent.py` | Chat with RAG agent — tool calls print inline |
| 5 | `docker compose down` | Clean up |

**Exercises:**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-build-index` | Chunk ship logs, embed with OpenAI, store in ChromaDB, interactive search |
| `exercises/02-rag-chat` | Grounded chat agent with source citations, /norag comparison |
| `exercises/03-rag-mcp-server` | Wrap RAG pipeline as MCP server, connect to tool-calling agent |

---

### Module 6 — Structured Facts

**Talk about:**

- Structured outputs with Pydantic models
- Fact extraction pipelines: claims, provenance, confidence
- Knowledge graphs: entities, relationships, traversal with networkx
- Grounded QA from graphs with citations

**Demo:**

Each demo is a separate interactive script with real OpenAI calls:

| Script | What it shows |
| ------ | ------------- |
| `module-06-structured-facts/demo/01_extraction.py` | Pydantic schema, structured extraction from logs, validation filtering |
| `module-06-structured-facts/demo/02_graph.py` | Build networkx graph from facts, query entities and paths |
| `module-06-structured-facts/demo/03_grounded_qa.py` | Graph-grounded QA with citations, comparison without graph |

**Exercises:**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-fact-extractor` | Extract structured facts with OpenAI + Pydantic, interactive REPL with /validate, /json, /schema |
| `exercises/02-knowledge-graph` | Build networkx graph from facts, query entities, find paths, explore connections |
| `exercises/03-grounded-qa` | Graph-grounded QA with [Fact N] citations, /evidence, /nograph comparison |

---

### Module 7 — Agent Memory

**Talk about:**

- Short-term (session) vs long-term (profile) memory
- Summarisation to fit context windows
- Memory decay and explicit "do not remember" controls

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-07-agent-memory/demo/demo.py` | All-in-one walkthrough: session memory, long-term memory with decay, summarisation, memory-enhanced agent |

**Exercises:**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-memory-store` | Session + long-term memory with decay/forget, interactive agent with /memories, /decay, /forget |
| `exercises/02-conversation-summary` | Auto-summarise long conversations, /summary, /turns, /force-summarise |
| `exercises/03-memory-server` | Memory as FastMCP server, console agent via stdio, /tools |

---

### Module 8 — Structured Workflows

Day 2 closer.

**Talk about:**

- ReAct pattern: Reason → Act → Observe loop
- Plan-and-execute workflows: generate plan, execute steps, re-plan on failure
- Comparison: when to use ReAct vs plan-and-execute
- Integration into web apps with SSE streaming

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-08-structured-workflows/demo/01_react.py` | ReAct loop with real tools — trace printed live |
| `module-08-structured-workflows/demo/02_plan_and_execute.py` | Plan generation, step execution, re-planning on failure |

**Exercises (chained — delegates build a Holiday Planner web app):**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-react-agent` | ReAct loop with web search, calculator, notes. /trace, /tools, /steps N |
| `exercises/02-plan-and-execute` | Planner + executor with re-planning. /plan, /react, /replan comparison |
| `exercises/03-holiday-planner` | FastAPI backend + Svelte frontend. SSE streaming, MCP tools, plan visualisation |

A Svelte frontend is provided. Delegates focus on the backend logic.

---

## Day 3 — Ship it

### Module 9 — Multi-Agent Systems

**Talk about:**

- When multi-agent helps vs hurts (latency, complexity trade-offs)
- Agent roles: router, researcher, coder, critic
- Coordination patterns: supervisor, swarm, debate, blackboard
- Shared context and tools across agents
- Consensus and conflict resolution

**Demo:** `python module-09-multi-agent/demo/demo.py` (single interactive file, five parts)

| Part | What it shows |
| ---- | ------------- |
| Part 1 | Specialist agents + LLM router |
| Part 2 | Supervisor-critic pipeline with revision loop |
| Part 3 | Structured debate with a judge |
| Part 4 | Consensus voting across specialists |
| Part 5 | Swarm handoffs with scoped tools |

**Exercises:**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-router-agent` | Route queries to medical, tactical, or comms specialists |
| `exercises/02-supervisor-critic` | Supervisor orchestrates specialists + critic |
| `exercises/03-consensus` | Debate, judge synthesis, and consensus voting |
| `exercises/04-swarm-tools` | Scoped tools and peer-to-peer handoffs between agents |

---

### Module 10 — LangChain with Python

**Talk about:**

- What LangChain provides vs building from scratch
- Chains, prompt templates, output parsers, LCEL
- Tool-calling agents: create_tool_calling_agent, AgentExecutor
- RetrievalQA chains for RAG
- LangServe: `add_routes` turns an LCEL chain into `/invoke`, `/stream`, and `/playground` on FastAPI
- Trade-offs: convenience vs control, debugging, vendor lock-in

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-10-langchain/demo/01_chains_and_prompts.py` | Prompt template + chain for classification |
| `module-10-langchain/demo/02_langchain_agents.py` | Wrap tools, run via AgentExecutor |
| `module-10-langchain/demo/03_langchain_rag.py` | RetrievalQA chain over knowledge base |
| `module-10-langchain/demo/04_langserve.py` | Deploy classification chain via LangServe; httpx in-process invoke |

**Exercises:**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-chain-basics` | Prompt template + chain for crew report classification |
| `exercises/02-tool-agent` | Wrap ship tools as LangChain tools, run via AgentExecutor |
| `exercises/03-rag-chain` | RetrievalQA chain over the Pathfinder knowledge base |
| `exercises/04-langserve-api` | FastAPI + LangServe `/classify` routes; health check; httpx tests |

---

### Module 11 — Edge Topics

**Talk about:**

- Advanced retrieval patterns: hybrid search, re-ranking, HyDE
- Agentic RAG: agent-driven retrieval with self-critique and citation verification
- Evaluation: automated LLM eval metrics, fine-tuning data pipelines
- Guardrails: input/output validation, safety filters
- Caching: semantic similarity caching for LLM responses
- And more: web search backends, text-to-SQL, multimodal RAG, contextual chunking
- This is a pick-and-choose module — delegates work on topics that interest them most

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-11-edge-topics/demo/demo.py` | Interactive walkthrough of hybrid search, agentic RAG, citation verification, semantic caching |

**Exercises (13 standalone exercises, one per topic):**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-hybrid-search` | Combine dense and sparse retrieval |
| `exercises/02-reranking` | Re-rank retrieved results for relevance |
| `exercises/03-hyde` | Hypothetical Document Embeddings for better retrieval |
| `exercises/04-agentic-rag` | Agent-driven retrieval with self-critique |
| `exercises/05-citation-verification` | Verify and ground citations in source documents |
| `exercises/06-web-search-backend` | Integrate web search as a retrieval source |
| `exercises/07-text-to-sql` | Natural language to SQL query generation |
| `exercises/08-llm-eval` | Evaluate LLM outputs with automated metrics |
| `exercises/09-fine-tuning-data` | Build datasets for fine-tuning |
| `exercises/10-guardrails` | Input/output validation and safety filters |
| `exercises/11-semantic-cache` | Cache LLM responses by semantic similarity |
| `exercises/12-multimodal-rag` | RAG with images and text |
| `exercises/13-contextual-chunking` | Context-aware document chunking strategies |

---

### Module 12 — Productionisation

**Talk about:**

- Production hardening: what changes between a prototype and a production AI system
- Structured tracing: trace IDs, spans, JSON logging, observability platforms
- Reliability: retries with exponential backoff + jitter, timeouts, circuit breakers, fallbacks
- Cost controls: token budgets (per-session, per-day), model tiering, caching, batching
- Deployment: Docker, health checks, environment config, secrets management
- Then hand off to capstone exercises — learners choose one app and build it

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-12-productionisation/demo/01_tracing.py` | TraceContext with spans, timing, JSON output |
| `module-12-productionisation/demo/02_circuit_breaker.py` | Circuit breaker states, failure handling, recovery |
| `module-12-productionisation/demo/03_cost_controls.py` | Token budgets, model tiering, cost tracking |

**Exercises (choose one):**

| Folder | What you build |
| ------ | -------------- |
| `exercises/01-recipe-finder` | RAG + hybrid search + multimodal vision + allergen guardrails |
| `exercises/02-movie-night` | RAG + text-to-SQL + reranking + chart data |
| `exercises/03-travel-planner` | Agentic RAG + tool calling + structured itineraries |
| `exercises/04-personal-assistant` | Chat + tools + MCP + RAG notes + calendar management |
