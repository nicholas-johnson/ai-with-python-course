# Exercise 04 — MCP Client

**Mission briefing:** You have built MCP servers. Now build a **client** that discovers tools on a server, validates arguments, calls a tool, and handles errors gracefully.

## Objectives

1. Implement `discover_tools` that queries a server's tool list and returns a name→schema mapping.
2. Implement `call_tool` that validates required arguments against the schema before sending the call.
3. Handle errors: return a structured error dict when the tool name is unknown or arguments are invalid.

## Run the tests

```bash
pytest module-03-mcp-server/exercises/04-mcp-client/test_start.py -v
```
