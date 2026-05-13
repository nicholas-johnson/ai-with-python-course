# Instructor Guide

## Day 1 — Build a working agent

### Module 1 — Working with the LLM

**Talk about:**

- Chat-completion API: message roles (system/user/assistant), sending a list, getting a response
- The chat loop pattern: while-loop, append user input, call API, append response
- Why streaming matters: perceived latency, first token in 200ms vs 3s blank screen
- Streaming with the OpenAI SDK: `stream=True`, iterating over chunks, `delta.content`
- Conversation persistence: JSON file save/load, slash commands for a CLI app
- SSE with FastAPI (lecture/demo only): EventSourceResponse for web frontends

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-01-working-with-the-llm/demo/01_chat_cli.py` | Live streaming CLI chat with real OpenAI API. Point out the message list growing. |
| `module-01-working-with-the-llm/demo/02_api_backend.py` | FastAPI server with SSE. Start it, curl POST to /chat, show event stream. |
| `module-01-working-with-the-llm/demo/03_session_storage.py` | Protocol-based pluggable storage. In-memory vs file. Same interface, different backends. |

**Exercises (chained — each builds on the previous):**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-first-chat` | First API call + console input loop. `python start.py` for interactive chat. |
| `exercises/02-streaming` | Streaming upgrade — tokens print as they arrive. Ships with ex01 solution. |
| `exercises/03-chat-app` | Slash commands (/clear, /history, /save, /load) + file persistence. Ships with ex02 solution. |

---

### Module 2 — Agent Core

**Talk about:**

- The 4th role: `tool` — model requests actions via tool_calls, you execute and feed results back
- The tool-calling loop: ask → tool? → execute → append result → ask again. Cap with max_steps.
- Tool registry: JSON Schema per tool, decorator registration, validate-then-call, list_tools() output
- Safety rails: allowlists, rate limits (sliding window), audit logging
- Golden-file evaluation (demo only): mock LLM, scripted responses, assert tools + answer

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-02-agent-core/demo/01_message_format.py` | Live API call that triggers a tool call. Walk through the 4 message roles in real time. |
| `module-02-agent-core/demo/02_tool_registry.py` | Decorator registration, list_tools(), call() with error handling. Unknown tool and bad args both handled. |
| `module-02-agent-core/demo/03_safety_rails.py` | Allowlist blocks delete_all_data, rate limiter kicks in on 4th call, clearance levels redacted, audit trail. |
| `module-02-agent-core/demo/04_eval_harness.py` | Mock LLM, golden case definition, run agent loop, pass/fail checks. |

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
| `module-03-mcp-server/demo/01_mcp_concepts.py` | Tool schemas as data structures. Walk through JSON: name, description, inputSchema. |
| `module-03-mcp-server/demo/02_minimal_server.py` | Working FastMCP server. Start it, show tools/list response. |
| `module-03-mcp-server/demo/03_practical_tools.py` | Sensor read, crew lookup, log search reading from JSON data files. |

**Exercises:**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-hello-mcp` | Minimal MCP server exposing one tool |
| `exercises/02-mcp-tools` | Three ship-system tools: sensor, crew, logs |
| `exercises/03-auth-observability` | Per-tool auth scopes + structured logging |
| `exercises/04-mcp-client` | Client that discovers tools, validates args, handles errors |

---

### Module 4 — GenAI Strategies

**Talk about:**

- Prompt engineering: be specific, system prompts as standing orders, few-shot examples (2-3 pairs)
- Structured outputs: `response_format={"type": "json_object"}`, Pydantic validation, schema in system prompt
- Model selection trade-offs: quality vs cost vs latency, tiered routing
- Token counting and budgets (lecture): tiktoken, truncate or summarise if over budget
- Multimodal: Vision API (base64 image in message, content parts), Whisper for audio transcription
- Guardrails (lecture): schema validation, content filter, confidence threshold — already practised in Module 2

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-04-genai-strategies/demo/01_prompting_patterns.py` | Structured output prompts, few-shot examples (skeleton for live walkthrough) |
| `module-04-genai-strategies/demo/02_model_selection.py` | Model comparison, cost calculation |
| `module-04-genai-strategies/demo/03_guardrails.py` | Validation chain: valid output passes, malformed JSON fails schema, toxic content fails filter |

**Exercises (chained — each builds on the previous):**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-structured-outputs` | Pydantic model + `response_format` + system prompt. Console app: type a description, get structured JSON. |
| `exercises/02-vision` | Base64 image encoding + GPT-4o vision. Console app: `python start.py image.png`. Ships with ex01 solution. |
| `exercises/03-multimodal-api` | FastAPI app with `/chat`, `/vision`, `/transcribe` endpoints. Day 1 closer — instructor provides web frontend. Ships with ex01+ex02 solution. |

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

| Script | What it shows |
| ------ | ------------- |
| `module-05-rag-fundamentals/demo/01_chunking.py` | Different chunking strategies on ship logs |
| `module-05-rag-fundamentals/demo/02_embeddings_vectors.py` | Embedding text, storing in vector index, similarity search |
| `module-05-rag-fundamentals/demo/03_retrieval_strategies.py` | Dense vs hybrid retrieval, reranking |

**Exercises:**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-document-chunker` | Chunk ship logs into overlapping windows |
| `exercises/02-vector-search` | Embed and search the mission archives |
| `exercises/03-rag-pipeline` | End-to-end RAG with citation linking |

---

### Module 6 — Multi-Agent Systems

**Talk about:**

- When multi-agent helps vs hurts (latency, complexity trade-offs)
- Agent roles: router, researcher, coder, critic
- Coordination patterns: supervisor, swarm, debate, blackboard
- Shared context and tools across agents
- Consensus and conflict resolution

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-06-multi-agent/demo/01_agent_roles.py` | Define and run agents with different roles |
| `module-06-multi-agent/demo/02_supervisor_pattern.py` | Supervisor delegates to specialists, synthesises results |
| `module-06-multi-agent/demo/03_debate_pattern.py` | Two agents argue, third votes |

**Exercises:**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-router-agent` | Route queries to navigation, engineering, or science specialists |
| `exercises/02-supervisor-critic` | Supervisor coordinates researcher + critic |
| `exercises/03-consensus` | Multiple agents propose answers, vote on best |

---

### Module 7 — Agent Memory + Workflows

**Talk about:**

- Short-term (session) vs long-term (profile) memory
- Summarisation to fit context windows
- Memory decay and explicit "do not remember" controls
- Workflow patterns: ReAct (Reason → Act → Observe), plan-and-execute

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-07-agent-memory/demo/01_memory_types.py` | Short-term buffer vs long-term store with decay |
| `module-07-agent-memory/demo/02_summarisation.py` | Compress long conversation to fit token budget |
| `module-07-agent-memory/demo/03_workflow_patterns.py` | ReAct loop and plan-and-execute side by side |

**Exercises:**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-memory-store` | Short-term buffer and long-term memory with decay |
| `exercises/02-conversation-summary` | Summarise long conversations to fit a token budget |
| `exercises/03-react-loop` | Implement ReAct: Reason, Act, Observe |

---

### Module 8 — Structured Facts

**Talk about:**

- Structured outputs with Pydantic models
- Fact extraction pipelines: claims, provenance, confidence
- Knowledge graphs: entities, relationships, traversal with networkx
- Grounded QA from graphs with citations

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-08-structured-facts/demo/01_structured_extraction.py` | Extract typed facts from unstructured text |
| `module-08-structured-facts/demo/02_knowledge_graph.py` | Build graph from entities, query relationships |
| `module-08-structured-facts/demo/03_grounded_qa.py` | Answer questions from graph with source citations |

**Exercises:**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-fact-extractor` | Extract structured facts from ship logs using Pydantic |
| `exercises/02-knowledge-graph` | Build a graph from entities, query relationships |
| `exercises/03-grounded-qa` | Answer questions with source citations and confidence |

---

## Day 3 — Ship it

### Module 9 — Adaptive Retrieval

**Talk about:**

- Retrieval routing: vector vs graph vs keyword based on query type
- Query decomposition: break complex questions into sub-queries
- Self-critique loops: corrective RAG, evaluate and re-retrieve
- Multi-source orchestration: fan-out, merge, rank

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-09-adaptive-retrieval/demo/01_retrieval_routing.py` | Route queries to different backends |
| `module-09-adaptive-retrieval/demo/02_self_critique.py` | Evaluate retrieval quality, refine query |
| `module-09-adaptive-retrieval/demo/03_multi_source.py` | Fan out to multiple sources, merge and rank |

**Exercises:**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-retrieval-router` | Route queries to vector, graph, or keyword search |
| `exercises/02-self-critique` | Evaluate retrieval quality and refine queries |
| `exercises/03-multi-source-qa` | Fan out, merge, rank, answer with citations |

---

### Module 10 — Production & Deployment

**Talk about:**

- Structured tracing: trace IDs, spans, attributing every call
- Reliability: retries with backoff, timeouts, circuit breakers, fallbacks
- Cost controls: token budgets, model tiering, caching, batching
- Deployment: environment config, secrets, Docker, health checks, CI/CD

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-10-production/demo/01_structured_tracing.py` | Trace IDs propagated through tool calls |
| `module-10-production/demo/02_circuit_breaker.py` | Circuit breaker opening after failures, fallback |
| `module-10-production/demo/03_deployment_pipeline.py` | Config per environment, health check endpoint |

**Exercises:**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-trace-middleware` | Add trace IDs and timing to every tool call |
| `exercises/02-batch-pipeline` | Batch LLM requests with retry and fallback model |
| `exercises/03-cost-tracker` | Per-session token and cost budget enforcement |
| `exercises/04-deploy-container` | Health-check app, env config, Dockerfile validation |

---

### Module 11 — LangChain with Python

**Talk about:**

- What LangChain provides vs building from scratch
- Chains, prompt templates, output parsers, LCEL
- Tool-calling agents: create_tool_calling_agent, AgentExecutor
- RetrievalQA chains for RAG
- Trade-offs: convenience vs control, debugging, vendor lock-in

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-11-langchain/demo/01_chains_and_prompts.py` | Prompt template + chain for classification |
| `module-11-langchain/demo/02_langchain_agents.py` | Wrap tools, run via AgentExecutor |
| `module-11-langchain/demo/03_langchain_rag.py` | RetrievalQA chain over knowledge base |

**Exercises:**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-chain-basics` | Prompt template + chain for crew report classification |
| `exercises/02-tool-agent` | Wrap ship tools as LangChain tools, run via AgentExecutor |
| `exercises/03-rag-chain` | RetrievalQA chain over the Pathfinder knowledge base |

---

### Module 12 — Capstone Project

**Talk about:**

- Architecture overview: chat → router → specialists → supervisor → guardrails → memory
- Integration testing: happy path, error handling, adversarial inputs
- Extension points: new tools, new agents, new retrieval sources, new guardrails

**Demo:**

| Script | What it shows |
| ------ | ------------- |
| `module-12-capstone/demo/01_architecture_overview.py` | Full system architecture walkthrough |
| `module-12-capstone/demo/02_demo_scenario.py` | End-to-end query through the full pipeline |

**Exercises:**

| Folder | Delegates build |
| ------ | --------------- |
| `exercises/01-capstone-app` | Integrated chat + RAG + MCP + multi-agent app |
| `exercises/02-test-and-extend` | Integration tests and extension documentation |
