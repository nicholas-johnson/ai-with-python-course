# Module 13 — Capstone Project

> Everything comes together here. Over thirteen modules you have built Python foundations, an agent core, LLM integration, prompt engineering, MCP tools, RAG pipelines, multi-agent coordination, memory systems, knowledge graphs, adaptive retrieval, production hardening, and LangChain chains. The capstone project integrates these into a single working application — the Pathfinder Operations AI — a full agentic system that the bridge crew can query about any aspect of the ship.

## Learning goals

- **Design** a complete agentic application architecture.
- **Integrate** RAG, multi-agent, MCP tools, memory, and guardrails in one system.
- **Demo** realistic operational scenarios with real data.
- **Test** with integration tests that cover happy paths and failure modes.
- **Document** extension points so future developers can add capabilities.

---

## Architecture overview

The capstone application is a layered system. Each layer corresponds to a module you have already completed:

```
Crew member
    ↓
[Chat API — FastAPI + SSE streaming]           (Module 1)
    ↓
[Router Agent — classifies and delegates]      (Module 9)
    ├── [RAG Agent — searches documents]       (Modules 5, 10)
    ├── [Tool Agent — calls MCP tools]         (Modules 1, 4)
    └── [Analyst Agent — structured facts]     (Module 6)
    ↓
[Supervisor — synthesises, critiques]          (Module 9)
    ↓
[Guardrails — validates output]               (Module 3)
    ↓
[Session memory — stores conversation]         (Module 7)
    ↓
Response to crew member
```

The user query enters through a FastAPI endpoint. The router agent classifies the query and delegates to one or more specialist agents. The supervisor collects results, runs them through guardrails, and returns a grounded answer. The conversation is stored in session memory for continuity.

---

## Key components

**Chat entrypoint** — a FastAPI app with SSE streaming (Module 1). The crew member sends a message; tokens stream back in real time. Tool calls appear as events so the user sees what the AI is doing.

**Router** — analyses the query and decides which specialist(s) to invoke (Module 9). A navigation question goes to the tool agent with sensor tools. A research question goes to the RAG agent. A complex question may fan out to multiple agents.

**RAG agent** — retrieves relevant documents from the vector store, applies adaptive retrieval routing (Module 10), and builds a grounded prompt with citations (Module 5).

**Tool agent** — discovers and calls MCP tools (Module 4). Sensor reads, crew lookups, and log searches are all available. Tool calls are validated against schemas and gated by auth scopes.

**Analyst agent** — extracts structured facts from tool results and RAG passages (Module 6). Builds or queries a knowledge graph for relationship questions.

**Supervisor** — orchestrates the workflow, runs critique loops, and assembles the final answer (Module 9). If the first answer is low-confidence, it triggers a revision.

**Guardrails** — validates the final response against schema, content filters, and confidence thresholds (Module 3). Rejected responses trigger a fallback.

**Memory** — session memory persists the conversation; long-term memory stores crew preferences (Module 7).

**Production hardening** — trace IDs propagate through every step, retries handle transient failures, cost tracking enforces budgets (Module 11).

---

## Demo scenarios

The capstone demo exercises the full system with realistic queries:

**Scenario 1 — Routine status check:**
"What is the current reactor status?" → Router sends to tool agent → MCP tool reads sensor → direct answer with source.

**Scenario 2 — Research question:**
"What do the logs say about the navigation anomaly last week?" → Router sends to RAG agent → adaptive retrieval searches logs → grounded answer with citations.

**Scenario 3 — Complex analysis:**
"Compare reactor performance before and after the ion storm and recommend maintenance actions." → Router fans out to RAG agent (retrieve logs) and tool agent (current readings) → analyst extracts structured facts → supervisor synthesises → guardrails validate → cited answer with recommendations.

**Scenario 4 — Failure handling:**
LLM API times out → circuit breaker opens → fallback to cached response → error is traced and logged.

---

## Integration testing

The capstone requires integration tests that exercise the full pipeline — not just unit tests on individual components.

**Happy path tests** — send a query, verify the response contains expected data, check that tool calls were made, and confirm citations are present.

```python
async def test_status_query():
    response = await app_client.post("/chat", json={"message": "Reactor status?"})
    assert response.status_code == 200
    data = response.json()
    assert "reactor" in data["answer"].lower()
    assert len(data["tool_calls"]) > 0
```

**Failure mode tests** — simulate LLM failures, tool errors, and empty retrieval results. Verify the system degrades gracefully — fallback responses, error messages, and no crashes.

**End-to-end flow tests** — send a multi-turn conversation and verify memory continuity. The second message should reference context from the first.

---

## Extension points

A well-designed capstone is not finished — it is extensible. Document the extension points so future developers (or future you) know where to add capabilities:

- **New tools** — add a new `@mcp.tool()` function to the MCP server. The router discovers it automatically.
- **New retrieval sources** — add a backend to the adaptive retrieval layer. Register it in the router's classification logic.
- **New agent roles** — define a new specialist agent with its own system prompt and tool access. Add it to the supervisor's delegation table.
- **New guardrails** — add a validation function to the guardrail chain. It runs in sequence with existing checks.
- **New memory backends** — implement the `SessionBackend` Protocol from Module 1. Swap in Redis, Postgres, or any other store.

---

## Running the capstone

```bash
# Install all dependencies (including optional groups)
uv sync --all-extras

# Run the application
uvicorn capstone:app --host 0.0.0.0 --port 8000

# Run integration tests
pytest module-13-capstone/ -v

# Run with Docker
docker build -t pathfinder-ai .
docker run -p 8000:8000 --env-file .env pathfinder-ai
```

---

## Field rules

- **Integration tests are not optional.** Unit tests verify components; integration tests verify the system.
- **Document extension points.** The capstone should be a starting point, not a dead end.
- **Trace everything in the demo.** Show the trace alongside the answer to demonstrate production-readiness.
- **Demo failures, not just successes.** Graceful degradation is the most impressive feature.

---

## Demos

```bash
python module-13-capstone/demo/01_architecture_overview.py
python module-13-capstone/demo/02_demo_scenario.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-capstone-app`](exercises/01-capstone-app/) | Build the integrated Pathfinder Operations AI. |
| [`exercises/02-test-and-extend`](exercises/02-test-and-extend/) | Write integration tests and document extension points. |

Run tests for this module:

```bash
pytest module-13-capstone/
```

## Slides

From repo root: `pnpm slides:13`, or `cd module-13-capstone/slides && pnpm dev`.

## Reference

- All modules 1-13 — this capstone integrates everything.
- [FastAPI](https://fastapi.tiangolo.com/)
- [OpenAI API](https://platform.openai.com/docs/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [LangChain](https://python.langchain.com/)
