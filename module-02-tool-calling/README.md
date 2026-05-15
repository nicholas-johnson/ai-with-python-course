# Module 2 — Tool Calling

> The Pathfinder's AI is not magic — it is a loop. Now that you can talk to the LLM, it is time to give it hands. A crew member asks a question, the model decides whether to think or act, and if it acts it calls a tool, reads the result, and loops until it has an answer. This module builds that loop from scratch using real OpenAI API calls, hardens it with a tool registry that validates every call, and adds safety rails so the agent cannot run amok.

## Learning goals

- Understand the **message format** that drives an agent (system, user, assistant, tool messages).
- Build a **tool-calling loop** with real OpenAI API calls: schema in, action out, result back, repeat.
- Implement a **tool registry** with decorator registration, routing, and error handling.
- Add **safety rails**: allowlists, rate limits, audit logs.

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
def run_agent(client, question, max_steps=5):
    messages = [system_msg, {"role": "user", "content": question}]

    for _ in range(max_steps):
        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages, tools=TOOLS,
        )
        message = response.choices[0].message

        if message.tool_calls:
            messages.append(message)
            for tc in message.tool_calls:
                result = execute_tool(tc.function.name, tc.function.arguments)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
        elif message.content:
            return message.content  # final answer

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

For regression testing, **mock the LLM** with scripted responses and check that the agent makes the right tool calls and produces the expected answer. Golden tests are fast (no API calls), free (no tokens), and deterministic (same result every run). See `demo/04_eval_harness.py` for the pattern.

---

## Field rules

- **Always cap loop iterations.** `max_steps` prevents runaway agents and surprise bills.
- **Validate before you execute.** Check the allowlist and schema before calling any tool handler.
- **Use golden tests for regression.** Real API calls for development, mocks for CI.

---

## Demos

```bash
python module-02-tool-calling/demo/demo.py
```

Walks through all four topics interactively — press Enter between sections:
1. **Message format** — live API call that triggers a tool call, traces all 4 roles
2. **Tool registry** — decorator registration, `list_tools()`, call routing, error handling
3. **Safety rails** — allowlist blocks `delete_all_data`, rate limiter kicks in, redaction, audit log
4. **Eval harness** — mock LLM, golden case, pass/fail checks (no API calls)

## Exercises

The exercises chain — each one builds on the previous. Run them with `python start.py` for an interactive CLI chat, or use `pytest` to validate.

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-tool-calling-agent`](exercises/01-tool-calling-agent/) | Build a tool-calling agent with real OpenAI API calls. |
| [`exercises/02-tool-registry`](exercises/02-tool-registry/) | Refactor with a decorator-based tool registry. |
| [`exercises/03-guarded-agent`](exercises/03-guarded-agent/) | Add allowlist, rate limiter, and audit log. |

Run tests for this module:

```bash
pytest module-02-tool-calling/
```

## Slides

From repo root: `pnpm slides:02`, or `cd module-02-tool-calling/slides && pnpm dev`.

## Reference

- [OpenAI function calling](https://platform.openai.com/docs/guides/function-calling)
- [JSON Schema](https://json-schema.org/)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
