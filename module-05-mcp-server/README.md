# Module 5 — MCP Server: Capabilities as Tools

**Standard protocols, standard power.** The Model Context Protocol (MCP) gives AI agents a uniform way to discover and call tools — no custom glue per integration. This module builds an MCP server from scratch, wires up real ship-system tools, and adds auth and observability.

## Learning goals

- Understand **MCP concepts**: tool discovery, schemas, calling conventions.
- Build a **minimal MCP server** in Python (hello tool, then real tools).
- Implement **practical tools**: filesystem (sandboxed), crew lookup, mission query, sensor read.
- Add **auth + permissions** (per-tool scopes) and **structured logging** for observability.

## Instructor notes

- **MCP concepts** (demo `01_mcp_concepts.py`): what MCP is, how it differs from raw function calling, the tool-discovery handshake.
- **Minimal server** (demo `02_minimal_server.py`): a single-tool MCP server using the `mcp` Python SDK. Run it, call it, see the response.
- **Practical tools** (demo `03_practical_tools.py`): multiple tools exposing ship data — show how the agent discovers and calls them.

## Demos

```bash
python module-05-mcp-server/demo/01_mcp_concepts.py
python module-05-mcp-server/demo/02_minimal_server.py
python module-05-mcp-server/demo/03_practical_tools.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-hello-mcp`](exercises/01-hello-mcp/) | Build a minimal MCP server that exposes one tool. |
| [`exercises/02-ship-tools`](exercises/02-ship-tools/) | Implement 3 ship-system tools: sensor read, crew lookup, log query. |
| [`exercises/03-auth-observability`](exercises/03-auth-observability/) | Add per-tool auth scopes and structured logging. |
| [`exercises/04-mcp-client`](exercises/04-mcp-client/) | Build an MCP **client**: discover tools, validate args, handle errors. |

Run tests for this module:

```bash
pytest module-05-mcp-server/
```

## Slides

From repo root: `pnpm slides:05`, or `cd module-05-mcp-server/slides && pnpm dev`.

## Reference

- [Model Context Protocol spec](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
