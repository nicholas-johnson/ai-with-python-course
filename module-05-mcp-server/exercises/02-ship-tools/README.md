# Exercise 02 — Ship Tools

**Mission briefing:** The Pathfinder AI needs access to ship systems. Build an MCP server with three tools: sensor readings, crew lookup, and log search. Each tool reads from the shared data files and returns structured JSON.

## Objectives

1. Register a `read_sensor` tool — takes `sensor_id`, returns a simulated reading.
2. Register a `query_crew` tool — takes optional `department`, returns matching crew.
3. Register a `search_logs` tool — takes `query` and optional `category`/`limit`, returns matching log entries.

## Run the tests

```bash
pytest module-05-mcp-server/exercises/02-ship-tools/test_start.py -v
```
