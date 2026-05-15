# Exercise 3: RAG MCP Server

## Recap

In Module 3 you built MCP servers that exposed tools. Now you'll wrap the RAG pipeline from Exercises 1 and 2 into an MCP server, then connect it to an agent.

This is a powerful pattern: your RAG system becomes a **pluggable capability** that any MCP-compatible agent can use. The agent doesn't need to know about embeddings, ChromaDB, or chunking -- it just calls `search_docs` or `ask_docs`.

The architecture:

```
User → Agent (OpenAI tool-calling) → MCP Client → MCP Server → RAG Pipeline → ChromaDB
```

The MCP server exposes four tools:

| Tool | Parameters | Returns |
|---|---|---|
| `search_docs` | `query: str, k: int = 5` | Top-k chunks with scores and metadata |
| `get_chunk` | `chunk_id: str` | Full text of a specific chunk |
| `ask_docs` | `question: str` | RAG-generated answer with citations |
| `list_sources` | (none) | List of all source document IDs |

## What you build

Two files:

1. **`server.py`** -- A FastMCP server that builds the index on startup and exposes RAG tools
2. **`start.py`** -- A console agent that connects to the server via stdio and uses OpenAI tool-calling

The Exercise 1 and 2 code (index builder + RAG chat) is already inlined at the top of `server.py` — you'll add the MCP tools below it.

## Step-by-step

### 1. Build `server.py`

Create a FastMCP server that initializes the index on module load and registers four tools:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("RAG Server")

# The index builder and RAG chat functions are already at the top of the file.
# Build the index at server startup:
logs = load_logs()
collection = build_index(logs)

@mcp.tool()
def search_docs(query: str, k: int = 5) -> str:
    """Search the document index for relevant passages."""
    hits = search(collection, query, k)
    # Format as readable text and return
    ...
```

Implement all four tools: `search_docs`, `get_chunk`, `ask_docs`, `list_sources`.

**Test the server standalone:**

```bash
python -m mcp dev server.py
```

This opens the MCP Inspector -- a web UI where you can call each tool and see raw responses.

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
- Run the standard tool-calling loop (send message → check for tool calls → execute → feed back)
- Print tool calls and results inline

### 3. Add the interactive commands

| Command | Action |
|---|---|
| any text | Chat with the agent (tool calls print inline) |
| `/tools` | List discovered MCP tools with descriptions |
| `quit` | Exit |

## Try it

```bash
cd module-05-rag-fundamentals/exercises/03-rag-mcp-server
python start.py
```

Ask questions about the ship logs. Watch the agent discover and call the RAG tools. Try asking it to search for specific topics, then dig into individual chunks.

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- The server registers the expected tools
- `search_docs` returns formatted results
- `ask_docs` returns a cited answer

## Stretch goals

- Add a `summarize_source` tool that summarises all chunks from a given source document
- Add a tool that compares two sources
- Expose the server over HTTP instead of stdio
