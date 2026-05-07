# Exercise 01 — Hello MCP

**Mission briefing:** Build your first MCP server. It exposes a single tool — `greet` — that takes a name and returns a personalised welcome message. The tests verify the tool is registered, has the right schema, and returns the correct output.

## Objectives

1. Create a `FastMCP` server instance.
2. Register a `greet` tool that accepts a `name` parameter and returns a greeting string.
3. Register a `ship_time` tool that takes no parameters and returns a fixed timestamp string.

## Run the tests

```bash
pytest module-05-mcp-server/exercises/01-hello-mcp/test_start.py -v
```
