# Exercise 01 -- MCP Agent

> Build an MCP server with ship tools, then wire it to a console agent that discovers and calls those tools dynamically. The agent never hard-codes tool definitions -- it asks the server what is available.

## Recap

In Module 2 you defined tools as JSON schemas inside the agent code. That works, but it means the agent and the tools are tightly coupled -- add a new tool and you have to update the agent. The **Model Context Protocol (MCP)** solves this with a standard protocol between the agent and the tool server. The agent connects, asks "what tools do you have?", and gets back tool schemas dynamically.

**Building an MCP server** is simple with `FastMCP`. You decorate Python functions and the framework generates JSON Schema from type hints:

```python
from mcp.server.fastmcp import FastMCP

server = FastMCP("Pathfinder Ship")

@server.tool()
def get_crew_count(department: str) -> str:
    """Get the number of crew members in a department."""
    return json.dumps({"department": department, "count": 3})
```

The docstring becomes the tool description. Type hints drive the parameter schema: `department: str` becomes `{"type": "string"}`. The server runs over **stdio transport** -- it communicates via stdin/stdout when launched as a subprocess.

**Connecting a client** uses the `mcp` package's client library. You spawn the server as a subprocess and open a session:

```python
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

server_params = StdioServerParameters(command=sys.executable, args=["server.py"])

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()        # discover tools
        result = await session.call_tool("name", arguments={...})  # call a tool
```

The key bridge is **converting MCP tool schemas to OpenAI format**. Each MCP tool has `.name`, `.description`, and `.inputSchema`. OpenAI expects `{"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}`. A simple list comprehension handles the conversion.

This exercise uses the `mcp` and `openai` packages, which are installed via the project's `pyproject.toml`.

## What you build

This exercise has **two files** to implement:

**`server.py`** -- a FastMCP server with 3 tools:
- `get_crew_count(department)` -- crew count for a department
- `get_ship_status(system)` -- system status lookup
- `search_crew(query)` -- search crew by name or role

**`start.py`** -- a console agent that:
1. Connects to `server.py` via MCP stdio
2. Discovers tools dynamically
3. Converts MCP schemas to OpenAI format
4. Runs a tool-calling chat loop

## Step-by-step

### Part A: `server.py` -- the MCP server

The server file already has the data (`CREW_DATA`, `SHIP_SYSTEMS`) and the `FastMCP` instance. You need to register 3 tools using the `@server.tool()` decorator.

#### A1. `get_crew_count(department: str) -> str`

Look up `CREW_DATA.get(department, [])` and return a JSON string with the department name and count:

```python
@server.tool()
def get_crew_count(department: str) -> str:
    """Get the number of crew members in a department."""
    crew = CREW_DATA.get(department, [])
    return json.dumps({"department": department, "count": len(crew)})
```

#### A2. `get_ship_status(system: str) -> str`

Look up `SHIP_SYSTEMS.get(system)`. If not found, return `{"system": system, "status": "unknown"}`. Otherwise return the full status dict as JSON.

#### A3. `search_crew(query: str) -> str`

Iterate over all departments in `CREW_DATA`. For each crew member, check if `query.lower()` appears in the name or role (case-insensitive). Return all matches as a JSON list, including the department.

### Part B: `start.py` -- the MCP agent

The `main()` function and MCP connection boilerplate are provided. You need to implement two pieces.

#### B1. `mcp_to_openai_tools(mcp_tools) -> list[dict]`

Convert a list of MCP Tool objects to OpenAI format. Each MCP tool has `.name`, `.description`, and `.inputSchema`. Map them to:

```python
{
    "type": "function",
    "function": {
        "name": tool.name,
        "description": tool.description or "",
        "parameters": tool.inputSchema,
    },
}
```

Handle `None` descriptions by defaulting to `""`.

#### B2. The tool-calling loop inside `run_agent()`

This is the same pattern as Module 2, but tool execution uses MCP instead of direct function calls:

1. Call `client.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=openai_tools)`.
2. If `message.tool_calls`:
   - Append the assistant message.
   - For each tool call: parse the arguments, call `await session.call_tool(name, arguments=args)`.
   - Extract the text: `result.content[0].text if result.content else ""`.
   - Append the tool result message.
3. Else if `message.content`: print and break.

Note the `await` -- `session.call_tool()` is async because it communicates with the server subprocess.

## Try it

```bash
python start.py
```

On startup you should see the discovered tools listed. Then try:

- `"How many crew in science?"` -- should call `get_crew_count`.
- `"What's the warp status?"` -- should call `get_ship_status`.
- `"Find anyone named Chen"` -- should call `search_crew` and find matches in multiple departments.
- `"quit"` -- exits.

## Tests

```bash
pytest module-03-mcp-server/exercises/01-mcp-agent/test_start.py -v
```

The tests check the server tools directly (via FastMCP internals) and the `mcp_to_openai_tools()` conversion function. They do not require a running MCP connection.

## Stretch goals

1. Add a `list_departments()` tool to the server and re-run -- the agent discovers it automatically without any changes to `start.py`.
2. Print the raw MCP tool schemas on startup so you can see what the agent is working with.
