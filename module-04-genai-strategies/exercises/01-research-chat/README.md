# Exercise 1: Research Chat — Streaming Chat with MCP Tools

## Recap

You're building the backend for a **Research Assistant** web app. A Svelte frontend is provided — your job is to wire up the FastAPI backend that streams chat from the OpenAI model (`gpt-6-luna` by default) and executes tools via a provided MCP server.

The key ingredients:

- **Server-Sent Events (SSE)** — a one-way channel from server to client over HTTP. The `sse-starlette` package provides `EventSourceResponse` which wraps an async generator into the correct wire format.
- **OpenAI streaming** — pass `stream=True` to `client.responses.create()` and iterate over the events:

```python
stream = client.responses.create(
    model=MODEL, reasoning={"effort": "none"}, input=messages, stream=True
)
for event in stream:
    if event.type == "response.output_text.delta":
        print(event.delta, end="", flush=True)
```

- **MCP tool discovery** — the backend connects to the MCP server at startup, calls `tools/list`, and converts the tools into OpenAI function tools (`{"type": "function", "name", "description", "parameters"}`).
- **Tool-calling loop** — when the LLM wants to call a tool, the backend executes it via MCP and feeds the result back. This loop repeats until the LLM produces a final text response.

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

| File        | Description                                                                              |
| ----------- | ---------------------------------------------------------------------------------------- |
| `server.py` | **Provided** — MCP server with 5 research tools (fetch_url, save/list/read/search notes) |
| `start.py`  | FastAPI app with streaming chat, tool-calling loop, and tool list endpoint               |

### SSE events

| Event         | Payload                                     | When                                      |
| ------------- | ------------------------------------------- | ----------------------------------------- |
| `token`       | `{"token": "Hello"}`                        | Each incremental piece of text            |
| `tool_call`   | `{"name": "fetch_url", "arguments": {...}}` | LLM requests a tool call                  |
| `tool_result` | `{"name": "fetch_url", "content": "..."}`   | Tool execution result                     |
| `done`        | `{"role": "assistant", "content": "..."}`   | The complete assistant message at the end |

## Step-by-step

### 1. Add the health endpoint

Quick warm-up:

```python
@app.get("/health")
async def health():
    return {"status": "ok"}
```

### 2. Convert MCP tools to OpenAI format

Implement `mcp_to_openai_tools(mcp_tools)`. Each MCP tool has `.name`, `.description`, and `.input_schema`. Convert to:

```python
{
    "type": "function",
    "name": tool.name,
    "description": tool.description,
    "parameters": tool.input_schema,
}
```

### 3. Implement `execute_tool_calls`

For each tool call from the LLM:

1. Extract `tc.name` and `json.loads(tc.arguments)`
2. Call `session.call_tool(name, args)` to execute it via MCP
3. Return a `{"type": "function_call_output", "call_id": tc.call_id, "output": ...}` dict

### 4. Add the tools endpoint

```python
@app.get("/tools")
async def list_tools():
    return [{"name": t.name, "description": t.description or ""} for t in mcp_conn.tools]
```

### 5. Build the `/chat` tool-calling loop

This is the main event. Replace the placeholder streaming code with a loop:

1. Call `client.responses.create()` **without** `stream=True` (you need to inspect the output for function calls)
2. If `response.output` contains `function_call` items:
   - Add the model's output to the conversation: `messages += response.output`
   - Yield `tool_call` SSE events for each tool call
   - Run them with `execute_tool_calls()`
   - Yield `tool_result` SSE events
   - Append results to messages and **loop again**
3. Otherwise (text response):
   - Make a **streaming** call to get the final answer token by token
   - Yield `token` events, then a `done` event with the full content
   - Break out of the loop

## Try it

Start the backend, then the frontend:

```bash
# Terminal 1 — backend
cd module-04-genai-strategies/exercises/01-research-chat
uvicorn solution:app --reload --port 8000

# Terminal 2 — frontend
cd module-04-genai-strategies/frontend
pnpm dev
```

Try asking: "Fetch the Wikipedia page about transformers and summarise the key points. Save a note with your summary."

You should see tool calls and results appearing in the chat, followed by the streamed response.

## Tests

```bash
pytest test_start.py -v
```

The tests check:

- `/health` returns 200 with the correct JSON
- `/tools` returns the MCP tool list
- `/chat` correctly streams tool events

## Stretch goals

- Add a `model` field to `ChatRequest` so the user can pick `gpt-6-luna` vs `gpt-6-sol`
- Add a system message that gives the assistant a research-focused personality
- Handle the case where `OPENAI_API_KEY` is not set with a friendly error
