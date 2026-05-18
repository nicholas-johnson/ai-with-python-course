# Exercise 03 — Memory MCP Server

## Recap

In Module 3 you built MCP servers that exposed tools. Now you'll wrap the memory system from Exercises 1 and 2 into an MCP server, then connect it to an agent via stdio.

This is the same architecture pattern you used for the RAG MCP server -- your memory system becomes a **pluggable capability** that any MCP-compatible agent can use. The agent doesn't need to know about decay, summarisation, or storage internals -- it just calls `remember`, `recall`, or `get_summary`.

The architecture:

```
Patron → BARKEEP Agent (OpenAI tool-calling) → MCP Client → MCP Server → Memory System
```

## The scenario

The Nebula's Edge is expanding. Management wants BARKEEP's memory to be a shared service -- other station systems (the concierge desk, the loyalty programme, the kitchen) should be able to remember things about patrons too. So you're extracting memory into an MCP server that any agent can connect to.

BARKEEP still chats with patrons directly, but now its memory lives behind MCP tools. If the kitchen agent needs to know "Chief Tanaka is allergic to synthcitrus", it calls the same `recall` tool.

## MCP tools

The MCP server exposes five tools:

| Tool | Parameters | Returns |
|---|---|---|
| `remember` | `key: str, value: str` | Confirmation message |
| `recall` | `query: str` | Matching memories formatted as text |
| `forget` | `key: str` | Confirmation or "not found" |
| `list_memories` | (none) | All active memories with importance scores |
| `get_summary` | (none) | Current conversation summary |

## What you build

Two files:

1. **`server.py`** -- A FastMCP server that manages memory and exposes tools
2. **`start.py`** -- A console agent that connects to the server via stdio and uses OpenAI tool-calling

The Exercise 1 and 2 solutions are provided as `memory_store.py` and `summary.py`.

## Step-by-step

### 1. Build `server.py`

Create a FastMCP server that initialises the memory system and registers five tools:

```python
from mcp.server.fastmcp import FastMCP
from memory_store import LongTermMemory
from summary import SmartSessionMemory

mcp = FastMCP("Cantina Memory")

long_term = LongTermMemory()
session = SmartSessionMemory(...)

@mcp.tool()
def remember(key: str, value: str) -> str:
    """Store a fact about a patron in long-term memory."""
    long_term.remember(key, value)
    return f"Remembered: {key} = {value}"
```

Implement all five tools: `remember`, `recall`, `forget`, `list_memories`, `get_summary`.

**Test the server standalone:**

```bash
python -m mcp dev server.py
```

This opens the MCP Inspector where you can call each tool and see raw responses.

### 2. Build `start.py`

Connect to the MCP server via `stdio_client`, discover tools, and run a tool-calling agent loop:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        # ... OpenAI tool-calling loop
```

The agent should:
- Convert MCP tools to OpenAI function format
- Run the standard tool-calling loop (send message, check for tool calls, execute, feed back)
- Print tool calls and results inline
- Use the memory tools naturally during conversation

### 3. Add the interactive commands

| Command | Action |
|---|---|
| any text | Chat with BARKEEP (tool calls print inline) |
| `/tools` | List discovered MCP tools with descriptions |
| `quit` | Exit |

## Try it

```bash
cd module-07-agent-memory/exercises/03-memory-server
python start.py
```

Chat with BARKEEP and share your drink order, your name, or a secret. The agent will use the `remember` tool to store them. Ask "what's my usual?" and watch it call `recall`. Use `/tools` to see the available memory tools.

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- The server registers the expected tools
- `mcp_to_openai_tools` converts MCP tools to OpenAI format
- The client module has the expected functions

## Stretch goals

- Add a `decay` tool that applies importance decay
- Add an `import_memories` tool that loads patron data from a JSON file
- Expose the server over HTTP instead of stdio
