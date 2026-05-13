# Exercise 02 -- Data Tools

> Build a richer MCP server that reads from the course JSON data files. The agent from Exercise 01 connects to it automatically -- you focus on the server.

## Recap

In Exercise 01 you built an MCP server with hardcoded data. That is fine for a hello-world, but real tools need to read from data sources. This exercise builds tools that query the course's shared data files: `crew.json`, `ship_logs.json`, and `missions.json`.

The pattern is the same -- decorate a function with `@server.tool()` and the framework handles the rest:

```python
@server.tool()
def query_crew(department: str | None = None) -> str:
    """Look up crew members, optionally filtering by department."""
    results = _crew
    if department:
        results = [m for m in results if m["department"].lower() == department.lower()]
    return json.dumps(results)
```

**Optional parameters** are supported via `str | None = None` in the type hint. FastMCP generates the correct JSON Schema -- the field appears in `properties` but not in `required`. This lets the model call the tool with or without the filter.

**Richer parameter schemas** emerge naturally from multiple parameters. A tool like `search_logs(keyword, category, limit)` gives the model fine-grained control over what to search for, how to filter, and how many results to return.

The data files live in the `data/` directory at the project root. The server loads them at startup with:

```python
DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
_crew = json.loads((DATA_DIR / "crew.json").read_text())
```

This exercise uses `mcp` and `json` (standard library). The agent code in `start.py` is provided from Exercise 01's solution -- it connects to your server and runs the chat loop. You only need to implement `server.py`.

## What you build

**`server.py`** -- a FastMCP server with 4 tools:
- `query_crew(department, role)` -- filtered crew lookup
- `search_logs(keyword, category, limit)` -- keyword search over ship logs
- `read_sensor(sensor_id)` -- simulated sensor reading
- `list_missions()` -- list all missions

**`start.py`** is provided (agent code from Exercise 01).

## Step-by-step

### 1. `query_crew(department: str | None = None, role: str | None = None) -> str`

Filter the `_crew` list by department and/or role:

1. Start with `results = _crew` (the full crew list).
2. If `department` is provided, filter to crew where `m["department"].lower() == department.lower()`.
3. If `role` is provided, filter to crew where `role.lower() in m["role"].lower()` (substring match).
4. Return a JSON list of `{"id": ..., "name": ..., "role": ..., "department": ...}` for each match.

The tests call `query_crew({})` to get all crew, `query_crew({"department": "science"})` to filter, and `query_crew({"department": "nonexistent"})` which should return `[]`.

### 2. `search_logs(keyword: str, category: str | None = None, limit: int = 5) -> str`

Search `_logs` by keyword:

1. If `category` is provided, filter logs where `log["category"].lower() == category.lower()`.
2. Filter to logs where `keyword.lower()` appears in `log["content"].lower()`.
3. Slice to `results[:limit]`.
4. Return as JSON.

The tests check keyword matching and the `limit` parameter.

### 3. `read_sensor(sensor_id: str) -> str`

Simulate a deterministic sensor reading:

1. Calculate the value: `(hash(sensor_id) % 1000) / 10.0`.
2. Determine status: `"nominal"` if value < 80, else `"warning"`.
3. Return JSON: `{"sensor_id": ..., "value": ..., "unit": "celsius", "status": ...}`.

Using `hash()` makes the reading deterministic -- same sensor ID always returns the same value. The tests check this.

### 4. `list_missions() -> str`

Return `_missions` as a JSON string: `json.dumps(_missions)`.

The tests check that the result is a non-empty list.

## Try it

```bash
python start.py
```

On startup, the agent discovers all 4 tools from the server. Try:

- `"Who is in the science department?"` -- should call `query_crew` with a department filter.
- `"Search the logs for anything about warp"` -- should call `search_logs`.
- `"Read sensor SEN-007"` -- should call `read_sensor` and return a temperature reading.
- `"What missions are on record?"` -- should call `list_missions`.
- `"Find Dr. Chen's department and the status of the sensors"` -- may call multiple tools in one turn.

## Tests

```bash
pytest module-03-mcp-server/exercises/02-data-tools/test_start.py -v
```

The tests check the server tools directly via FastMCP internals and verify tool discovery.

## Stretch goals

1. Add a `count_crew(department: str | None = None)` tool that returns just the count, not the full records.
2. Add a `recent_logs(hours: int = 24)` tool that filters logs by timestamp (if the data has timestamps).
