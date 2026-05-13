# Exercise 2: MCP-Powered Research Tools

## Recap

In Module 3 you built MCP servers and connected them to agents. Now you'll integrate the same pattern into a web API. The key pieces:

- **MCP server** -- a FastMCP server that exposes research tools (web fetching, note-taking). It runs as a subprocess spawned by the FastAPI backend.
- **Tool discovery** -- at startup, the backend connects to the MCP server, calls `tools/list`, and converts the tools into OpenAI's function-calling format.
- **Tool-calling loop** -- when the LLM wants to call a tool, the backend executes it via MCP and feeds the result back. This loop repeats until the LLM produces a final text response.
- **SSE events** -- in addition to `token` and `done`, the backend now streams `tool_call` and `tool_result` events so the frontend can display tool activity.

The MCP client connection uses `mcp.client.stdio`:

```python
from mcp.client.stdio import stdio_client, StdioServerParameters

server_params = StdioServerParameters(command="python", args=["server.py"])
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
```

## What you build

Two files:

| File | Description |
|---|---|
| `server.py` | MCP server with 5 research tools |
| `start.py` | Extended FastAPI app with tool-calling chat + `/tools` endpoint |

### MCP tools to implement

| Tool | Parameters | Description |
|---|---|---|
| `fetch_url` | `url: str` | Fetch a web page, strip HTML, return text |
| `save_note` | `title: str, content: str` | Save a research note to `notes/` directory |
| `list_notes` | (none) | List all saved notes |
| `read_note` | `title: str` | Read a saved note by title |
| `search_notes` | `query: str` | Search notes by keyword |

### New SSE events

| Event | Payload | When |
|---|---|---|
| `tool_call` | `{"name": "fetch_url", "arguments": {...}}` | LLM requests a tool call |
| `tool_result` | `{"name": "fetch_url", "content": "..."}` | Tool execution result |

## Step-by-step

### 1. Build `server.py` -- the MCP server

Create a FastMCP server with the 5 tools listed above:

```python
from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("Research Tools")

@mcp.tool()
async def fetch_url(url: str) -> str:
    """Fetch a web page and return its text content."""
    # TODO: use httpx to fetch, strip HTML tags, truncate to ~5000 chars
    pass
```

For note tools, store files in a `notes/` directory next to the server. Sanitise filenames to prevent path traversal.

### 2. Copy the Exercise 1 solution into `start.py`

Your `start.py` begins with the working chat API from Exercise 1.

### 3. Connect to the MCP server on startup

Use FastAPI's lifespan to spawn the MCP server and discover tools:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    # Connect to MCP server, store session + tools on app.state
    yield
    # Cleanup

app = FastAPI(lifespan=lifespan)
```

### 4. Convert MCP tools to OpenAI format

Write a helper function:

```python
def mcp_to_openai_tools(mcp_tools):
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            },
        }
        for tool in mcp_tools
    ]
```

### 5. Extend `/chat` with a tool-calling loop

When the LLM returns `tool_calls` instead of content:

1. Yield a `tool_call` SSE event for each call
2. Execute the tool via the MCP session
3. Yield a `tool_result` SSE event with the result
4. Feed the result back into the messages and call the LLM again
5. Repeat until the LLM returns text content

### 6. Add `GET /tools`

Return the list of available tools:

```python
@app.get("/tools")
async def list_tools():
    return [{"name": t.name, "description": t.description} for t in app.state.mcp_tools]
```

## Try it

```bash
# Terminal 1
cd module-04-genai-strategies/exercises/02-tool-chat
uvicorn start:app --reload --port 8000

# Terminal 2
cd module-04-genai-strategies/frontend
pnpm dev
```

Try asking: "Fetch the Wikipedia page about transformers and summarise the key points. Save a note with your summary."

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- MCP server starts and exposes the expected tools
- `/tools` endpoint returns the tool list
- `/chat` correctly streams tool events

## Stretch goals

- Add a `summarise_url` tool that fetches and summarises in one step
- Add rate limiting to `fetch_url` to prevent abuse
- Store notes with timestamps and allow sorting by date
