# Exercise 01 — ReAct Agent

## Recap

**ReAct** (Reason + Act) is the foundational pattern for tool-using LLM agents. Instead of answering in one shot, the model follows a loop:

1. **Thought** — the model reasons about what to do next
2. **Action** — it calls a tool with specific arguments
3. **Observation** — it sees the tool's output
4. **Repeat** — until it has enough information to answer

OpenAI's tool-calling API maps naturally to ReAct. When you pass `tools=` to `responses.create`, the model can choose to return `function_call` items instead of (or alongside) text. You execute those calls, feed the results back as `function_call_output` items, and loop until the model responds with a final answer.

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model=MODEL,
    reasoning={"effort": "none"},
    input=messages,
    tools=tool_schemas,
)
calls = [item for item in response.output if item.type == "function_call"]

if calls:
    # Execute tools, append results, call again
    ...
else:
    # Final answer in response.output_text
    ...
```

The **trace** — the sequence of thoughts, tool calls, and observations — is what makes ReAct agents debuggable. You can inspect exactly why the model did what it did.

## What you build

A console app in **`start.py`** that runs a ReAct agent with four tools:

| Tool | Description |
|---|---|
| `search_web(query)` | Search the web using DuckDuckGo Lite (or mock results) |
| `calculator(expression)` | Evaluate a mathematical expression safely |
| `take_note(content)` | Save a note to in-memory storage |
| `read_notes()` | Retrieve all saved notes |

The agent prints the full Thought → Action → Observation trace for every query.

## Step-by-step

### 1. Implement the tools

Each tool is a plain Python function that returns a string:

- **`search_web`**: Use `httpx` to GET `https://lite.duckduckgo.com/lite?q={query}` and extract text snippets. Fall back to a simple mock response if the request fails.
- **`calculator`**: Safely evaluate the expression. Only allow digits, operators (`+`, `-`, `*`, `/`, `**`), parentheses, decimal points, and spaces.
- **`take_note`**: Append to the `_notes` list, return a confirmation string.
- **`read_notes`**: Return all notes as a numbered list, or `"No notes yet."` if empty.

### 2. Define tool schemas

Build the `TOOL_SCHEMAS` list — one OpenAI function-calling schema per tool:

```python
{
    "type": "function",
    "name": "search_web",
    "description": "Search the web for information. Returns a text summary.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"}
        },
        "required": ["query"],
    },
}
```

### 3. Implement `run_react`

This is the core loop:

1. Start with `[SYSTEM_PROMPT, {"role": "user", "content": query}]`
2. Call `client.responses.create(model=MODEL, reasoning={"effort": "none"}, input=messages, tools=TOOL_SCHEMAS)`
3. If `response.output` has `function_call` items:
   - Add the model's output to the history: `messages += response.output`
   - For each call, look up the function in `TOOLS`, parse the JSON arguments, call it
   - Append each result as a `{"type": "function_call_output", "call_id": call.call_id, "output": result}` item
   - Add to the trace: `{"type": "tool", "name": name, "args": args, "result": result}`
   - Loop back to step 2
4. If there are no function calls, `response.output_text` is the final answer
   - Add to trace: `{"type": "answer", "content": content}`
5. Return `{"answer": str, "trace": list}`
6. Enforce `max_steps` — if you hit the limit, return whatever you have

### 4. Implement `print_trace`

Pretty-print each step:

```
[Step 1] 🔧 Tool: search_web({"query": "population of France"})
         → France has a population of approximately 68 million...

[Step 2] 🔧 Tool: calculator({"expression": "68000000 / 551695"})
         → 123.24...

[Step 3] ✅ Answer: The population density of France is about 123 people per km².
```

### 5. Build the interactive loop

Handle these commands:

| Command | Action |
|---|---|
| any text | Run the ReAct agent, print trace + answer |
| `/trace` | Re-display the last trace |
| `/tools` | List available tools |
| `/steps N` | Set the max steps for the loop |
| `quit` | Exit |

## Try it

```bash
cd module-08-structured-workflows/exercises/01-react-agent
python start.py
```

Try queries that require multiple tool calls:
- "What is the population of Japan divided by 1000?"
- "Search for the speed of light and save it in a note"
- "What notes do I have?"

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- `calculator` returns correct numeric results
- `take_note` / `read_notes` store and retrieve notes
- `TOOL_SCHEMAS` is a non-empty list of tool definitions
- `run_react` returns a dict with `"answer"` and `"trace"` keys

## Stretch goals

- Add a `get_weather(city)` tool using a public API
- Implement a `/history` command that shows the full message list sent to OpenAI
- Add token counting to show how many tokens each ReAct loop consumed
