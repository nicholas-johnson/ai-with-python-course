# Exercise 03 — Auth + Observability

**Mission briefing:** Not every officer should access every tool. Build an auth layer that checks per-tool scopes before execution, and add structured logging so Ops can track every tool call through the system.

## Objectives

1. Implement `AuthContext` dataclass — holds `user_id`, `role`, and `scopes` (set of strings).
2. Implement `check_scope(context, required_scope)` — returns True if the user has the required scope.
3. Implement `AuthenticatedToolRunner` — wraps tool calls with scope checks and structured logging.
4. Each tool call should produce a structured log dict: `{timestamp, user_id, tool, arguments, allowed, result_preview}`.

## Run the tests

```bash
pytest module-05-mcp-server/exercises/03-auth-observability/test_start.py -v
```
