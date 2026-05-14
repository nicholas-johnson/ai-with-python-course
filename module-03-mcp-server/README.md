# Module 3 — MCP Server

> The Pathfinder AI can answer questions about the ship, but only if the data is already in its context window. Real ship systems — sensor arrays, crew databases, maintenance logs — live behind APIs. The Model Context Protocol (MCP) gives LLMs a standard way to discover and call those APIs. In this module you build MCP servers of increasing power and wire each one to a console agent that discovers tools dynamically.

## Learning goals

- Understand the **Model Context Protocol**: tool discovery, schemas, calling conventions.
- Build **FastMCP servers** with practical tools: data queries, web fetch, file I/O.
- Connect an MCP server to a **real agent** via `mcp.client.stdio`.
- Convert MCP tool schemas to **OpenAI tool-calling format** for dynamic discovery.

---

## What is MCP?

The Model Context Protocol is a standard JSON-RPC interface between an LLM host (like a chat agent) and a tool server. Instead of hard-coding tool definitions in the agent, the host asks the server "what tools do you have?" at startup. The server responds with tool names, descriptions, and JSON Schema parameter definitions. When the LLM wants to call a tool, the host sends a JSON-RPC request to the server and streams the result back.

The benefit is **loose coupling**: add a new tool to the server and the agent discovers it automatically on next connection. No prompt editing, no agent redeployment. This is the pattern behind Cursor's MCP integration and many production agent architectures.

**Key concepts:**

| Concept | Role |
| ------- | ---- |
| **Server** | Exposes tools via JSON-RPC (`tools/list`, `tools/call`) |
| **Tool schema** | JSON Schema describing each tool's parameters |
| **Host** | The agent runtime that connects to one or more servers |
| **Transport** | How messages travel: stdio, HTTP+SSE, or WebSocket |

---

## Building a FastMCP server

The `mcp` Python package provides `FastMCP`, a high-level server class that handles protocol details. You define tools as decorated functions — the decorator generates the JSON Schema from type hints automatically.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Pathfinder")

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
python -m mcp run server.py
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

## Authentication — scopes and gating

Not every crew member should access every tool. MCP supports authentication through scopes — labels like `sensors:read`, `crew:read`, `logs:admin` that gate access.

```python
class AuthContext:
    def __init__(self, user_id: str, scopes: set[str]):
        self.user_id = user_id
        self.scopes = scopes

def check_scope(ctx: AuthContext, required: str) -> bool:
    return required in ctx.scopes
```

Before executing a tool, the server checks whether the caller's context includes the required scope. Rejected calls return a structured error — the agent can explain to the user why access was denied rather than failing silently.

---

## Structured logging — audit everything

Every tool call — allowed or rejected — should be logged with a structured JSON record. This is how you debug incidents, prove compliance, and measure usage.

```python
{
    "timestamp": "2287-03-15T14:30:00Z",
    "user_id": "CRW-001",
    "tool": "query_crew",
    "arguments": {"department": "science"},
    "allowed": true,
    "result_preview": "[{name: Voss}, {name: Orin}]"
}
```

Key fields: `timestamp` for ordering, `user_id` for attribution, `tool` and `arguments` for reproduction, `allowed` for the gate decision, and `result_preview` (truncated) so you can debug without logging full payloads. Never log sensitive data in full — truncate or hash.

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

## Field rules

- **Let the schema speak.** Type hints generate JSON Schema — keep functions simple and well-typed.
- **Gate before you execute.** Check scopes, then validate, then call.
- **Log everything structurally.** JSON logs beat free-text for querying and alerting.

---

## Demos

```bash
python module-03-mcp-server/demo/demo.py
```

Walks through all three topics interactively — press Enter between sections:
1. **MCP concepts** — tool discovery, schemas, calling conventions (data walkthrough, no server)
2. **FastMCP server** — decorator pattern, type hints to JSON Schema, auto-generated tool definitions
3. **Connecting a client** — spawns a real MCP server, discovers tools, converts to OpenAI format, runs a live tool-calling agent loop

## Exercises

Each exercise builds an MCP server (`server.py`) and runs it via a console agent (`start.py`). `python start.py` is interactive. Exercises chain: Exercise 2 ships with Exercise 1's agent, Exercise 3 ships with Exercise 1+2's solutions.

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-mcp-agent`](exercises/01-mcp-agent/) | Build a FastMCP server + console agent that connects via MCP stdio. |
| [`exercises/02-data-tools`](exercises/02-data-tools/) | Build a server that queries crew, logs, sensors, and missions from JSON data. |
| [`exercises/03-live-tools`](exercises/03-live-tools/) | Build a server that fetches web pages and manages notes on disk. |

Run tests for this module:

```bash
pytest module-03-mcp-server/
```

## Slides

From repo root: `pnpm slides:03`, or `cd module-03-mcp-server/slides && pnpm dev`.

## Reference

- [Model Context Protocol spec](https://modelcontextprotocol.io/)
- [FastMCP (Python)](https://github.com/modelcontextprotocol/python-sdk)
- [MCP — Cursor integration](https://docs.cursor.com/context/model-context-protocol)
