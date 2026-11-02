# Module 3 — MCP Server

> The Pathfinder AI can answer questions about the ship, but only if the data is already in its context window. Real ship systems — sensor arrays, crew databases, maintenance logs — live behind APIs. The Model Context Protocol (MCP) gives LLMs a standard way to discover and call those APIs. In this module you build MCP servers of increasing power and wire each one to a console agent that discovers tools dynamically.
> `

## Learning goals

- Understand the **Model Context Protocol**: tool discovery, schemas, calling conventions.
- Build **MCP servers** with `MCPServer` and practical tools: data queries, web fetch, file I/O.
- Connect an MCP server to a **real agent** via `mcp.client.stdio`.
- Convert MCP tool schemas to **OpenAI tool-calling format** for dynamic discovery.

---

## What is MCP?

The Model Context Protocol is a standard JSON-RPC interface between an LLM host (like a chat agent) and a tool server. Instead of hard-coding tool definitions in the agent, the host asks the server "what tools do you have?" at startup. The server responds with tool names, descriptions, and JSON Schema parameter definitions. When the LLM wants to call a tool, the host sends a JSON-RPC request to the server and streams the result back.

The benefit is **loose coupling**: add a new tool to the server and the agent discovers it automatically on next connection. No prompt editing, no agent redeployment. This is the pattern behind Cursor's MCP integration and many production agent architectures.

**Key concepts:**

| Concept         | Role                                                    |
| --------------- | ------------------------------------------------------- |
| **Server**      | Exposes tools via JSON-RPC (`tools/list`, `tools/call`) |
| **Tool schema** | JSON Schema describing each tool's parameters           |
| **Host**        | The agent runtime that connects to one or more servers  |
| **Transport**   | How messages travel: stdio or Streamable HTTP           |

> **Spec revision 2026-07-28.** The latest MCP spec drops the per-connection session (`Mcp-Session-Id`) so any server instance can answer any request, and adds `server/discover` for fetching capabilities on demand. The Python SDK v2 used in this course speaks both the new revision and older ones, so the `session.initialize()` call in our client code still works. The older HTTP+SSE transport is deprecated, and the SDK has dropped WebSocket support.

---

## Building an MCP server with `MCPServer`

The `mcp` Python package (v2) provides `MCPServer`, a high-level server class that handles protocol details. (In v1 of the SDK this class was called `FastMCP` — you will still see that name in older tutorials.) You define tools as decorated functions — the decorator generates the JSON Schema from type hints automatically.

```python
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("Pathfinder")

@mcp.tool()
def greet(name: str) -> str:
    """Greet a crew member by name."""
    return f"Welcome aboard, {name}."

@mcp.tool()
def ship_time() -> str:
    """Return the current ship time (UTC)."""
    return "2287-03-15T14:30:00Z"
```

Type hints drive schema generation: `name: str` becomes `{"type": "string"}` in the tool schema. Docstrings become tool descriptions. The framework validates incoming arguments against the schema before calling your function.

Run it with:

```bash
# Option A (venv active):
mcp run server.py
# Option B (uv):
uv run mcp run server.py
```

Or from code with `mcp.run(transport="stdio")` for local development and testing.

---

## Practical tools — sensors, crew, logs

A demo server is nice, but the Pathfinder needs real tools. Here are three patterns that cover the most common agent-tool interactions:

**Sensor reads** — point queries against a data source. The tool takes a sensor name and returns a structured reading.

```python
@mcp.tool()
def read_sensor(sensor_name: str) -> dict:
    """Read the current value of a ship sensor."""
    reading = SENSOR_DATA.get(sensor_name)
    if not reading:
        return {"error": f"Unknown sensor: {sensor_name}"}
    return {"sensor": sensor_name, "value": reading["value"], "unit": reading["unit"]}
```

**Crew lookup** — filtered queries. The tool accepts optional filters (department, clearance level) and returns matching records.

```python
@mcp.tool()
def query_crew(department: str | None = None, min_clearance: int = 0) -> list[dict]:
    """Look up crew members, optionally filtered by department and clearance."""
    results = CREW
    if department:
        results = [c for c in results if c["department"] == department]
    results = [c for c in results if c["clearanceLevel"] >= min_clearance]
    return results
```

**Log search** — keyword search over structured records. Returns matching entries with source and timestamp for citation.

```python
@mcp.tool()
def search_logs(keyword: str, limit: int = 5) -> list[dict]:
    """Search ship logs for entries containing the keyword."""
    matches = [log for log in SHIP_LOGS if keyword.lower() in log["entry"].lower()]
    return matches[:limit]
```

---

## Building an MCP client

The other side of the protocol is a **client** that connects to an MCP server, discovers its tools, and calls them. This is what the agent runtime does under the hood.

```python
class MCPClient:
    def __init__(self, tools: list[dict]):
        self._tools = {t["name"]: t for t in tools}

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def get_schema(self, name: str) -> dict:
        return self._tools[name]["inputSchema"]

    def call(self, name: str, arguments: dict) -> dict:
        schema = self.get_schema(name)
        self._validate(arguments, schema)
        return self._execute(name, arguments)
```

The client validates arguments locally before sending them over the wire — this catches errors early and saves a round trip. Unknown tool names raise a clear error. Schema validation checks required fields and types.

---

## Summary

- **MCP is discovery plus a schema.** The server advertises tools. The agent validates arguments and calls them.
- **Schema is documentation.** If the schema is wrong, the agent will call it wrong. Type hints generate the JSON Schema.
- **stdio locally, HTTP remotely.** A local process uses stdio. A remote server uses Streamable HTTP.
- **Fail soft, and sanitise inputs.** Return JSON errors, never crash. Never trust filenames, URLs, or queries.

---

## Demos

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python module-03-mcp-server/demo/demo.py

# Option B - uv (no activation needed):
uv run python module-03-mcp-server/demo/demo.py
```

Menu. Parts 3 and 4 need `http_server.py` running in another terminal.

1. **List tools** — connect to the ship server, print the names
2. **Ship server (stdio)** — discovery, then call each tool
3. **Navigation server (HTTP)** — the same, over a URL
4. **Multi-server agent** — one model, both servers

## Exercises

Each exercise builds an MCP server (`server.py`) and runs it via a console agent (`start.py`). `python start.py` is interactive. Exercises chain: Exercise 2 ships with Exercise 1's agent, Exercise 3 ships with Exercise 1+2's solutions.

| Folder                                                | Mission                                                                       |
| ----------------------------------------------------- | ----------------------------------------------------------------------------- |
| [`exercises/01-mcp-agent`](exercises/01-mcp-agent/)   | Build an `MCPServer` + console agent that connects via MCP stdio.           |
| [`exercises/02-data-tools`](exercises/02-data-tools/) | Build a server that queries crew, logs, sensors, and missions from JSON data. |
| [`exercises/03-live-tools`](exercises/03-live-tools/) | Build a server that fetches web pages and manages notes on disk.              |

Run tests for this module:

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pytest module-03-mcp-server/

# Option B - uv (no activation needed):
uv run --extra dev pytest module-03-mcp-server/
```

## Slides

From repo root: `pnpm slides:03`, or `cd module-03-mcp-server/slides && pnpm dev`.

## Reference

- [Model Context Protocol spec](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) — [v1 → v2 migration guide](https://py.sdk.modelcontextprotocol.io/migration/)
- [MCP — Cursor integration](https://cursor.com/docs/mcp)
