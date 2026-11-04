# Instructor Guide

> **Running commands:** every `python …` and `pytest …` command below assumes students set up with **Option A** (pip + venv) and have the repo-root venv active (`source .venv/bin/activate`). If they chose **Option B** (uv), the same commands work prefixed with `uv run` — e.g. `uv run python start.py`, `uv run --extra dev pytest`. See the root [README](README.md#setup) for both setup paths.

## Day 1 — Build a working agent

### Module 1 — Working with the LLM

**Talk about:**

- Chat Completions, the older API: `client.chat.completions.create(messages=...)`, reply at `choices[0].message.content`. Still everywhere — old code, tutorials, and "OpenAI-compatible" providers.
- The Responses API: `client.responses.create(input=..., instructions=...)`, reply at `response.output_text`. `instructions` stays separate from the conversation.
- Why Responses: one reply field, optional `previous_response_id` so you need not resend history, built-in tools, and where new features ship.
- The chat loop: a chatbot is a loop. `while True` because the number of turns is not known ahead of time — append user input, call the API, append the response.
- Why streaming matters: perceived latency, first token in 200ms vs 3s blank screen
- Streaming with the OpenAI SDK: `stream=True`, iterating over typed events, `response.output_text.delta` → `event.delta`
- Prompt engineering: personas, format constraints, guardrails, few-shot examples

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-01-working-with-the-llm/demo/01_completions.py` | One Chat Completions call, print the reply, exit. |
| `module-01-working-with-the-llm/demo/02_responses.py` | One Responses API call, print the reply, exit. Same question as the Completions script. |
| `module-01-working-with-the-llm/demo/demo.py` | The same walkthrough from a menu. 1 Chat Completions. 2 Responses. 3 The chat loop. 4 Streaming. 5 Prompt engineering. |

**Exercises (chained — each builds on the previous):**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-first-chat` | First API call + console input loop. `python start.py` for interactive chat. |
| `exercises/02-streaming` | Streaming upgrade — tokens print as they arrive. Ships with ex01 solution. |
| `exercises/03-prompting` | Write system prompts for 6 challenges (persona, format, JSON, haiku, guardrails, few-shot). Ships with run_prompt() helper. |

---

### Module 2 — Tool Calling

**Talk about:**

- Function-call items: the model returns `function_call` items in `response.output`; you execute them and send `function_call_output` items back, matched by `call_id`
- The tool-calling loop: ask → tool? → execute → append result → ask again. Cap with max_steps.
- Tool registry: JSON Schema per tool, decorator registration, validate-then-call, list_tools() output
- Safety rails: allowlists, rate limits (sliding window), audit logging
- Golden-file evaluation (demo only): mock LLM, scripted responses, assert tools + answer

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-02-tool-calling/demo/demo.py` | Menu. 1 One tool call. 2 Message flow. 3 Tool registry. 4 Guarded agent (allowlist, rate limit, redaction, audit). |

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
- MCPServer (formerly FastMCP): decorator-based, auto-generates schemas from type hints
- Practical tools: sensor reads, crew lookups, log search
- Auth and scopes: per-tool access control, token-based scoping
- Structured logging: every tool call logged with timestamp, caller, args, result, duration
- Building a client: discover tools dynamically, validate args, handle errors

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-03-mcp-server/demo/demo.py` | Menu. 1 List tools on the ship server. 2 Explore that server over stdio. 3 Explore the navigation server over HTTP (`http_server.py` in another terminal). 4 One agent, both servers. 5 Chat with local weather and TV rating servers. |

**Exercises (chained — each builds on the previous):**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-mcp-agent` | `MCPServer` + console agent connected via MCP stdio. `python start.py` for interactive chat. |
| `exercises/02-data-tools` | Richer server reading crew, logs, sensors, missions from JSON files. Ships with ex01 agent. |
| `exercises/03-live-tools` | Server with web fetch (httpx) + note save/list/read. Ships with ex01 agent. The "it actually does stuff" moment. |

---

### Module 4 — GenAI Strategies

**Talk about:**

- Prompt engineering: be specific, system prompts as standing orders, few-shot examples (2-3 pairs)
- Structured outputs: `client.responses.parse(text_format=PydanticModel)` → `response.output_parsed`; refusals (`output_parsed` is `None`); why it beats JSON mode (`json_object` + schema in the prompt)
- Model selection trade-offs: quality vs cost vs latency, tiered routing
- Token counting and budgets (lecture): tiktoken, truncate or summarise if over budget
- Multimodal: Vision API (base64 image in message, content parts), gpt-transcribe for audio transcription
- Guardrails (lecture): schema validation, content filter, confidence threshold — already practised in Module 2
- FastAPI + SSE streaming for real-time chat backends

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-04-genai-strategies/demo/demo.py` | Menu. 1 One image, one sentence. 2 The same image parsed into a schema. 3 Speech to text. |
| `module-04-genai-strategies/demo/04_tiktoken.py` | Token counting and cost, no API key. |

**Exercises (chained — delegates build a Research Assistant web app):**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-chat-api` | FastAPI backend with SSE streaming `/chat` and `/health`. Frontend chat panel lights up. |
| `exercises/02-tool-chat` | MCP server with web fetch + notes tools. Extend chat with tool-calling loop. Frontend shows tool activity. |
| `exercises/03-multimodal` | Add `/vision` (image analysis) and `/transcribe` (gpt-transcribe). Frontend image/audio uploads work. |

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
| 3 | `mcp dev server.py` | (Optional) MCP Inspector — call RAG tools in browser |
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
- Expose that graph as an MCP server so an agent loop chooses the traversal

**Demo:**

Each demo is a separate interactive script with real OpenAI calls:

| Script | What it shows |
| ------ | ------------- |
| `module-06-structured-facts/demo/01_extraction.py` | Pydantic schema, structured extraction from logs, validation filtering |
| `module-06-structured-facts/demo/02_graph.py` | Build networkx graph from facts, query entities and paths |
| `module-06-structured-facts/demo/03_grounded_qa.py` | Graph-grounded QA with citations, comparison without graph |
| `module-06-structured-facts/demo/graph_server.py` | Saved graph as an MCP server: list, neighbours, shortest path, facts within N hops |
| `module-06-structured-facts/demo/04_graph_agent.py` | Spawns the graph server and runs an agent loop. Part 1 calls `shortest_path` with no model. Part 2 watches the model choose tools. Part 3 is open chat. |

**Exercises:**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-fact-extractor` | Extract structured facts with OpenAI + Pydantic, interactive REPL with /validate, /json, /schema |
| `exercises/02-knowledge-graph` | Build networkx graph from facts, query entities, find paths, explore connections |
| `exercises/03-grounded-qa` | Graph-grounded QA with [Fact N] citations, /evidence, /nograph comparison |

---

### Module 7 — Agent Memory and Context Engineering

**Talk about:**

- The context window as a budget with competing claims: system prompt, tools, retrieved documents, memories, history
- Context rot — accuracy falling as the window fills, and worst in the middle
- Write: what is worth remembering, and resolving a contradiction on write instead of storing both
- Select: semantic recall scored on relevance plus recency plus importance, with relevance normalised before blending
- Compress: compaction with named anchors, and the three ways it breaks
- Memory and compaction as services rather than as parts of the agent

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-07-agent-memory/demo/demo.py` | Menu. 1 Where the budget goes, and what truncation costs. 2 Semantic recall with the score broken down. 3 Writer that skips, replaces, and stores. 4 Compaction against truncation on the same thread. 5 Agent with all of it wired together. |

Parts 1 and 4 run offline. Part 1 shows truncation dropping the decision that the whole evening hangs on; part 4 shows compaction keeping it as an anchor for roughly a third of the tokens.

**Exercises:**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-memory-store` | Chroma-backed semantic recall, blended scoring, typed write decisions that supersede, agent with /memories, /recall, /forget |
| `exercises/02-compaction` | Token counting over tool items, `safe_split`, anchors, budget-triggered `compact`, agent with /seed, /budget, /anchors, /compact |
| `exercises/03-memory-server` | One MCPServer over both families, stdio console agent, harness-driven compaction and context rebuild, /tools |

---

### Module 8 — Structured Workflows

Day 2 closer.

**Talk about:**

- The control-flow spectrum: fixed chain → router → plan-and-execute → ReAct. The question is not "ReAct or planning?" but how many decisions you hand to the model, since each one is untestable. Push left until the task breaks.
- ReAct: Reason → Act → Observe. Note this is Module 2's loop plus a visible thought — and that reading the thought off `output_text` gives you a blank field, because it is empty whenever the model emits a tool call. Fix with a required `thought` on a structured schema.
- Loop control: step budget, no-progress detection (and why it must reset after a mutating tool), forced finalisation, cost ceiling.
- Plan-and-execute: generate plan, execute steps, re-plan on failure. The payoff is that the plan is *data*.
- `depends_on` turns the plan into a graph — independent steps run concurrently. ReAct structurally cannot do this.
- Approval gates and checkpointing. Code decides what is dangerous, never the model.
- Integration into web apps with SSE streaming.

**Demo:** menu runner at `module-08-structured-workflows/demo/demo.py`; each part also runs standalone.

| Script | What it shows |
| ------ | ------------- |
| `demo/01_control_flow.py` | One task, four strategies — comparison table of LLM calls, tokens, seconds, model decisions |
| `demo/02_react.py` | ReAct with a required `thought`; second half runs a deliberately stuck model so the guards fire (no API key needed for that part) |
| `demo/03_plan_and_execute.py` | Plan generation, step execution, re-planning on failure |
| `demo/04_parallel_plan.py` | `depends_on` scheduled into waves; serial vs parallel wall-clock |
| `demo/05_approval_resume.py` | Halts before an irreversible step, checkpoints to JSON, resumes after approval |

Tools are shared in `demo/workflow_tools.py` so demo 01 compares strategies like for like. They sleep to simulate network calls — set `DEMO_TOOL_LATENCY=0` to speed up a dry run.

**Exercises (chained — delegates build a Holiday Planner web app):**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-react-agent` | ReAct loop with web search, calculator, notes, plus the three guards. /trace, /tools, /steps N |
| `exercises/02-plan-and-execute` | Planner + executor with re-planning. /plan, /react, /replan comparison |
| `exercises/03-parallel-approval` | `depends_on` waves via `asyncio.gather`, approval gate on `book_flight`, JSON checkpoint and resume |
| `exercises/04-holiday-planner` | FastAPI backend + Svelte frontend. SSE streaming, MCP tools, plan visualisation |

A Svelte frontend is provided. Delegates focus on the backend logic.

Run tests per exercise — a bare `pytest module-08-structured-workflows/` cannot collect, because every exercise has a `test_start.py` and there are no package markers (true of every module).

---

## Day 3 — Ship it

### Module 9 — Multi-Agent Systems

**Talk about:**

- When multi-agent helps vs hurts (latency, complexity trade-offs)
- Agent roles: router, researcher, coder, critic
- Coordination patterns: supervisor, swarm, debate, blackboard
- Shared context and tools across agents
- Consensus and conflict resolution
- Spawning subagents: context isolation, parallel fan-out, subagents as tools, reconciling reports

**Demo:** `python module-09-multi-agent/demo/demo.py`

| Part | What it shows |
| ---- | ------------- |
| Part 1 | One question, routed to one specialist |
| Part 2 | Supervisor-critic pipeline with revision loop |
| Part 3 | Structured debate with a judge |
| Part 4 | Consensus voting across specialists |
| Part 5 | Swarm handoffs with scoped tools |
| Part 6 | Subagents spawned on demand: serial vs parallel, spawn-as-tool, reconciled reports |

**Exercises:**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-router-agent` | Route queries to medical, tactical, or comms specialists |
| `exercises/02-supervisor-critic` | Supervisor orchestrates specialists + critic |
| `exercises/03-consensus` | Debate, judge synthesis, and consensus voting |
| `exercises/04-swarm-tools` | Scoped tools and peer-to-peer handoffs between agents |
| `exercises/05-subagents` | Spawn researchers from a tool, fan out concurrently, reconcile conflicting reports |

---

### Module 10 — LangChain with Python

**Talk about:**

- What LangChain provides vs building from scratch
- Chains, prompt templates, LCEL
- Structured output: `model.with_structured_output(PydanticModel)` vs output parsers (`JsonOutputParser` still wins for streaming partial results)
- Tool-calling agents: `create_agent` (LangChain 1.x, runs on LangGraph; replaces `AgentExecutor`)
- Agent middleware (`@wrap_tool_call`, `ToolCallLimitMiddleware`; built-ins for human approval, PII, retries) and memory via a checkpointer + `thread_id`
- LCEL RAG chains that return answer + sources from one retrieval (`RunnablePassthrough.assign`), then agentic RAG: the retriever as a tool
- Serving a chain: FastAPI routes that call `ainvoke` / `abatch` / `astream` (LangServe is unmaintained)
- Trade-offs: convenience vs control, debugging, vendor lock-in

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-10-langchain/demo/01_chains_and_prompts.py` | Prompt template + chain; structured output with a Pydantic schema; swap the last step (structured vs JSON parser vs string, incl. streaming partial JSON) |
| `module-10-langchain/demo/02_langchain_agents.py` | Wrap tools, run via `create_agent`; middleware part (tool-call logging + call limit); memory part (checkpointer, two threads) |
| `module-10-langchain/demo/03_langchain_rag.py` | LCEL RAG chain returning answer + sources; agentic RAG part with a `search_logs` tool |
| `module-10-langchain/demo/04_serving_chains.py` | Serve the classification chain with FastAPI (invoke / batch / stream); httpx in-process invoke |

**Exercises:**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-chain-basics` | Structured-output chain (`Classification` schema) for crew report classification; /stream, /raw, /batch, /compare |
| `exercises/02-tool-agent` | Wrap ship tools as LangChain tools, run via `create_agent` |
| `exercises/03-rag-chain` | LCEL RAG chain returning answer + sources, then agentic RAG (agent from 02 + `search_logs` tool) |
| `exercises/04-chain-api` | FastAPI `/classify/invoke` route over the chain; health check; httpx tests |

---

### Module 11 — Evals

**Talk about:**

- Why a live demo is not an eval: frozen test sets, CI vs token spend
- Golden tests: freeze the question + accepted outcome, then re-run and compare. The key point to land — the golden file holds *only* the reference; what the agent does comes from the build under test. A fixture that also scripts the agent just confirms the script matched itself and passes forever. Demo makes this concrete with two builds against one reference. Then: tool calls exact-match cleanly, prose does not (same facts, different words), so exact-match tools and judge the answer.
- Retrieval metrics: recall@k, precision@k, MRR on a labelled query set
- LLM-as-judge: correctness, completeness, relevance (JSON, temperature 0)
- Faithfulness: claims grounded in retrieved context, not the gold answer
- Scorecard + gate: pick a winner, fail a release below a floor
- The Module 12 capstones (exercises 04–07) can reuse the harness as a release check

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-11-evals/demo/demo.py` | Menu, no API key. 1 Golden tests (two agent builds vs one frozen reference; build B drops a tool call and paraphrases an answer). 2 Retrieval metrics. 3 Judge scores. 4 Faithfulness. 5 Scorecard + gate. `a` runs all five. |

**Exercises (chained — each adds a measurement the next one can consume):**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-golden-tests` | Mock-LLM agent-loop regression (score tools + answer, run a suite); README wires `run_case` + the ex03 judge into a live golden eval |
| `exercises/02-retrieval-metrics` | recall@k, precision@k, MRR on labelled ship-log queries |
| `exercises/03-llm-judge` | LLM-as-judge: correctness, completeness, relevance |
| `exercises/04-faithfulness` | Claim extraction + support check + faithfulness ratio |
| `exercises/05-eval-compare` | Scorecard two configs, pick a winner, gate a release |

---

### Module 12 — Productionisation

**Talk about:**

- Production hardening: what changes between a prototype and a production AI system
- Structured tracing: trace IDs, spans, JSON logging, observability platforms
- Reliability: retries with exponential backoff + jitter, timeouts, circuit breakers, fallbacks
- Cost controls: token budgets (per-session, per-day), model tiering, caching, batching
- Deployment: Docker, health checks, environment config, secrets management
- Capstones: learners pick one of exercises 04–07 and build its FastAPI backend against a provided SvelteKit frontend. Module 11's eval harness can serve as the release check.

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-12-productionisation/demo/01_tracing.py` | TraceContext with spans, timing, JSON output |
| `module-12-productionisation/demo/02_circuit_breaker.py` | Circuit breaker states, failure handling, recovery |
| `module-12-productionisation/demo/03_cost_controls.py` | Token budgets, model tiering, cost tracking |

**Exercises:**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-tracing` | `TraceContext` with nested spans and one JSON log line per span |
| `exercises/02-reliability` | Retry with backoff and jitter, a circuit breaker, and a fallback chain |
| `exercises/03-cost-controls` | Token budgets, a model-tiering router, and a prompt cache |
| `exercises/04-recipe-finder` | RAG + hybrid search + multimodal vision + allergen guardrails |
| `exercises/05-movie-night` | RAG + text-to-SQL + reranking + chart data |
| `exercises/06-travel-planner` | Agentic RAG + tool calling + structured itineraries |
| `exercises/07-personal-assistant` | Chat + tools + MCP + RAG notes + calendar management |

---

### Module 13 — Edge Topics

**Talk about:**

- Advanced retrieval patterns: hybrid search, re-ranking, HyDE
- Agentic RAG: agent-driven retrieval with self-critique and citation verification
- Local ML: fine-tuning data, CPU training, running Hugging Face models (eval lives in Module 11)
- Guardrails: input/output validation, safety filters
- Caching: semantic similarity caching for LLM responses
- And more: web search backends, text-to-SQL, multimodal RAG, contextual chunking
- Concepts only (slides 15–18): test-time compute, speculative decoding, GraphRAG, MoE
- This is a pick-and-choose module — delegates work on topics that interest them most

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-13-edge-topics/demo/demo.py` | Menu. 1 RRF on two short lists (no API). 2 Hybrid search. 3 Agentic RAG. 4 Citation verification. 5 Semantic cache. |
| `module-13-edge-topics/demo/13_*.py`, `14_*.py` | Local ML on CPU: train a classifier, fine-tune SmolLM2, run Hub models |

**Exercises (standalone labs; exercise numbers match topic numbers 1–14 in the README and slides; eval lives in Module 11):**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-hybrid-search` | Combine dense and sparse retrieval |
| `exercises/02-reranking` | Re-rank retrieved results for relevance |
| `exercises/03-hyde` | Hypothetical Document Embeddings for better retrieval |
| `exercises/04-agentic-rag` | Agent-driven retrieval with self-critique |
| `exercises/05-citation-verification` | Verify and ground citations in source documents |
| `exercises/06-web-search-backend` | Integrate web search as a retrieval source |
| `exercises/07-text-to-sql` | Natural language to SQL query generation |
| `exercises/08-guardrails` | Input/output validation and safety filters |
| `exercises/09-semantic-cache` | Cache LLM responses by semantic similarity |
| `exercises/10-multimodal-rag` | RAG with images and text |
| `exercises/11-contextual-chunking` | Context-aware document chunking strategies |
| `exercises/12-fine-tuning-data` | Build datasets for fine-tuning |
| `exercises/13-local-training` | Fine-tune a small classifier on CPU |
| `exercises/14-huggingface-run` | Run a Hub model with tokenizer + model, no `pipeline` |

