# Module 2 — Agent Core

> The Pathfinder's AI is not magic — it is a loop. A crew member asks a question, the model decides whether to think or act, and if it acts it calls a tool, reads the result, and loops until it has an answer. This module builds that loop from scratch, hardens it with a tool registry that validates every call, adds safety rails so the agent cannot run amok, and finishes with an evaluation harness that catches regressions before they reach the bridge.

## Learning goals

- Understand the **message format** that drives an agent (system, user, assistant, tool messages).
- Build a **tool-calling loop**: schema in, action out, result back, repeat.
- Implement a **tool registry** with schema validation, routing, and error handling.
- Add **safety rails**: allowlists, rate limits, redaction, audit logs.
- Write an **evaluation harness**: golden tests, replay, deterministic mocks.

---

## Message roles — the conversation state

Every agent conversation is a list of messages. Each message has a **role** that tells the model who said it:

- **system** — sets the agent's personality, constraints, and available tools. Sent once at the start.
- **user** — the human (or upstream agent) input.
- **assistant** — the model's response. Can contain text, tool calls, or both.
- **tool** — the result of executing a tool, linked back to the call by `tool_call_id`.

```python
messages = [
    {"role": "system", "content": "You are the Pathfinder AI..."},
    {"role": "user", "content": "Who is on the Kepler Sweep?"},
    {"role": "assistant", "tool_calls": [
        {"id": "c1", "name": "query_crew", "arguments": {"active_mission": "MSN-001"}}
    ]},
    {"role": "tool", "tool_call_id": "c1",
     "content": '[{"name": "Voss"}, {"name": "Chen"}, {"name": "Morel"}, {"name": "Kwan"}]'},
    {"role": "assistant",
     "content": "4 crew assigned to Kepler Sweep: Voss, Chen, Morel, Kwan."},
]
```

The model decides whether to call a tool or answer directly. Tool results come back as messages — the model interprets them, not us. This is the fundamental pattern behind every agent framework.

---

## The tool-calling loop

The core loop is deceptively simple. Ask the model. If it wants to call a tool, execute the tool, append the result, and ask again. If it replies with text, return it.

```python
def run_tool_loop(llm, tools, user_input, max_steps=10):
    messages = [system_msg, {"role": "user", "content": user_input}]

    for _ in range(max_steps):
        response = llm.chat(messages)

        if response.tool_calls:
            for tc in response.tool_calls:
                result = tools[tc.name](**tc.arguments)
                messages.append(...)  # assistant + tool messages
        elif response.content:
            return response.content  # final answer

    return None  # exhausted steps
```

`max_steps` is critical. Without it, a confused model can loop forever — calling tools that return unhelpful results, then calling them again with the same arguments. Always cap iterations.

---

## Tool registry pattern

A tool registry is the single source of truth for what the agent can do. Each tool declares a **JSON Schema** describing its name, description, and parameters. The registry validates arguments before calling the handler, routes by name, and catches exceptions so one broken tool does not crash the loop.

```python
registry = ToolRegistry()

@registry.register(
    name="ship_status",
    description="Get current status of a ship system",
    parameters={
        "type": "object",
        "properties": {
            "system": {"type": "string"}
        },
        "required": ["system"],
    },
)
def ship_status(system: str) -> dict:
    return {"system": system, "status": "online", "efficiency": 0.97}
```

The decorator pattern keeps the schema next to the handler — when you change the function, the schema is right there to update too. The registry's `list_tools()` method returns OpenAI-compatible tool definitions that you pass to the chat API.

```python
tools_for_api = registry.list_tools()
# [{"type": "function", "function": {"name": "ship_status", ...}}]
```

When the model returns a tool call, the registry validates the arguments against the schema and routes to the correct handler. Unknown tool names and bad arguments return structured error messages instead of crashing.

---

## Safety rails

LLMs can hallucinate tool names, call tools in harmful sequences, or leak sensitive data into responses. Safety rails are not optional — they are engineering requirements.

**Allowlists** restrict which tools the agent can call. If `delete_all_data` is not in the allowlist, the call is rejected before it reaches any handler.

**Rate limits** prevent runaway loops or cost explosions. A sliding-window limiter tracks recent call timestamps and blocks when the count exceeds the threshold:

```python
class RateLimiter:
    def __init__(self, max_calls: int, window: float):
        self.max_calls = max_calls
        self.window = window
        self._timestamps: list[float] = []

    def allow(self) -> bool:
        now = time.time()
        self._timestamps = [t for t in self._timestamps if now - t < self.window]
        if len(self._timestamps) >= self.max_calls:
            return False
        self._timestamps.append(now)
        return True
```

**Redaction** strips sensitive data (clearance levels, API keys) from logs and audit trails. **Audit logging** records every tool call — allowed or blocked — so you can debug incidents and prove compliance.

| Unguarded | Guarded |
| --------- | ------- |
| Any tool name accepted | Allowlist: only approved tools |
| No call frequency limits | Rate limiter: N calls per window |
| Secrets leak to logs | Redaction: sensitive data masked |
| No record of what happened | Audit trail: every call logged |

---

## Evaluation — golden-file testing

You cannot test an agent with live LLM calls — they are slow, expensive, and non-deterministic. Instead, **mock the LLM** with scripted responses and check that the agent makes the right tool calls and produces the expected answer.

A **golden case** is a fixed input paired with expected tool calls and answer:

```python
case = GoldenCase(
    name="crew count query",
    user_input="How many in science?",
    expected_tool_names=["get_crew_count"],
    expected_answer_contains="3",
)

result = run_golden_test(case, agent_fn)
assert result.passed
```

Golden tests are fast (no API calls), free (no tokens), and deterministic (same result every run). They catch regressions when you change prompts or tool schemas. Add a new case every time you discover an edge case — the suite only gets stronger.

---

## Field rules

- **Always cap loop iterations.** `max_steps` prevents runaway agents and surprise bills.
- **Validate before you execute.** Check the allowlist and schema before calling any tool handler.
- **Test with mocks, not live LLMs.** Golden tests are fast, deterministic, and free.

---

## Demos

```bash
python module-02-agent-core/demo/01_message_format.py
python module-02-agent-core/demo/02_tool_registry.py
python module-02-agent-core/demo/03_safety_rails.py
python module-02-agent-core/demo/04_eval_harness.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-tool-loop`](exercises/01-tool-loop/) | Build a minimal tool-calling loop: schema in, action out, result back. |
| [`exercises/02-tool-registry`](exercises/02-tool-registry/) | Implement a tool registry with validation and routing. |
| [`exercises/03-safety-eval`](exercises/03-safety-eval/) | Add rate limiting + write golden-file tests for a tool agent. |

Run tests for this module:

```bash
pytest module-02-agent-core/
```

## Slides

From repo root: `pnpm slides:02`, or `cd module-02-agent-core/slides && pnpm dev`.

## Reference

- [OpenAI function calling](https://platform.openai.com/docs/guides/function-calling)
- [JSON Schema](https://json-schema.org/)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
