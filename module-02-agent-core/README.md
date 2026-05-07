# Module 2 — Agent Core: A Minimal Tool-Using Loop

**The Pathfinder's AI isn't magic — it's a loop.** Receive a message, decide whether to think or act, call a tool if needed, feed the result back, and repeat. This module builds that loop from scratch, then hardens it with a tool registry, safety rails, and an evaluation harness.

## Learning goals

- Understand the **message format** that drives an agent (system, user, assistant, tool messages).
- Build a **tool-calling loop**: schema in, action out, result back, repeat.
- Implement a **tool registry** with schema validation, routing, and error handling.
- Add **safety rails**: allowlists, rate limits, redaction, audit logs.
- Write an **evaluation harness**: golden tests, replay, deterministic mocks.

## Instructor notes

- **Message format** (demo `01_message_format.py`): walk through the conversation state object — roles, tool calls, structured outputs. Show how the LLM "sees" tool results.
- **Tool registry** (demo `02_tool_registry.py`): registering tools with JSON schemas, validating arguments, routing calls, and handling errors gracefully.
- **Safety rails** (demo `03_safety_rails.py`): why agents need guardrails — allowlisted tools, rate limiting per tool, redacting sensitive data from logs, audit trail.
- **Eval harness** (demo `04_eval_harness.py`): golden-file testing (expected input/output pairs), replaying conversations, mocking LLM responses for deterministic tests.

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
