# Exercise 02 — MCP Tools

Build an MCP server with three practical tools: sensor read, crew lookup, and log search. Each tool reads from shared JSON data files and returns structured output.

## Objectives

1. Register a `read_sensor` tool — takes `sensor_id`, returns a simulated reading.
2. Register a `query_crew` tool — takes optional `department`, returns matching crew.
3. Register a `search_logs` tool — takes `query` and optional `category`/`limit`, returns matching log entries.

## Run the tests

```bash
pytest module-05-mcp-server/exercises/02-mcp-tools/test_start.py -v
```
