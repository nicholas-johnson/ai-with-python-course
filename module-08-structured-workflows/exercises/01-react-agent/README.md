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

The **trace** — the sequence of tool calls and observations — is what makes ReAct agents debuggable. You can inspect exactly why the model did what it did.

> **A warning about the Thought.** With native tool calling, `response.output_text` is usually **empty** whenever the model emits a `function_call`. So if you read the "Thought" off `output_text`, you get a blank line on every step that actually did something. Demo `02_react.py` shows the fix — make `thought` a required field on a structured response schema. This exercise stays with native tool calling, because exercises 02-04 build on it, so your trace records tool calls and the final answer.

## What you build

A console app in **`start.py`** that runs a ReAct agent with four tools:

| Tool | Description |
|---|---|
| `search_web(query)` | Search the web using DuckDuckGo Lite (or mock results) |
| `calculator(expression)` | Evaluate a mathematical expression safely |
| `take_note(content)` | Save a note to in-memory storage |
| `read_notes()` | Retrieve all saved notes |

The agent prints the full Action → Observation trace for every query — and, crucially, it is **guarded**, so it cannot run forever, go in circles, or come back empty-handed.

## Loop control: the three guards

An unguarded loop is the single most common way an agent ruins a production afternoon. Yours needs all three:

| Guard | Problem it solves | How |
|---|---|---|
| **1. Step budget** | Unbounded cost and latency | Loop at most `max_steps` times |
| **2. No-progress detection** | The model repeats a call it already made, burning the budget on an observation it has already seen | Track a signature of every `(name, args)` you execute. On a repeat, skip the tool and feed back a nudge instead |
| **2b. …but not blindly** | A repeat is only pointless if *nothing changed*. `read_notes()` after a new `take_note()` is a perfectly sensible repeat | Reset `seen` whenever a tool in `MUTATING_TOOLS` runs |
| **3. Forced finalisation** | Hitting the budget returns `None`, which is worse than a partial answer | On exhaustion, make one final call without tools asking the model to answer with what it has |

`run_react` returns `{"answer": str, "trace": list, "stop_reason": str}`, where `stop_reason` is `"answered"` or `"budget_exhausted"`.

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

1. Start with `[SYSTEM_PROMPT, {"role": "user", "content": query}]`, plus `seen = set()` to remember which calls you have executed
2. Loop at most `max_steps` times — **guard 1**
3. Call `client.responses.create(model=MODEL, reasoning={"effort": "none"}, input=messages, tools=TOOL_SCHEMAS)`
4. If `response.output` has `function_call` items:
   - Add the model's output to the history: `messages += response.output`
   - For each call, build `signature = (name, json.dumps(args, sort_keys=True))`
     - **If `signature` is already in `seen`** — **guard 2** — do *not* run the tool. Use a nudge string as the result (`"You already called {name} with these arguments..."`) and trace `{"type": "guard", "name": name, "args": args}`
     - Otherwise add it to `seen`, look up the function in `TOOLS`, call it, and trace `{"type": "tool", "name": name, "args": args, "result": result}`
   - Either way, append `{"type": "function_call_output", "call_id": call.call_id, "output": result}` to `messages`
   - Loop back to step 3
5. If there are no function calls, `response.output_text` is the final answer
   - Trace `{"type": "answer", "content": content}` and return with `stop_reason="answered"`
6. If the loop runs out of steps — **guard 3** — append a user message saying so, make one final call **without** `tools=`, trace the answer, and return it with `stop_reason="budget_exhausted"`

The nudge in guard 2 matters: silently dropping the call leaves the model wondering why nothing happened. Telling it "you already did this, do something else" is what gets it unstuck.

### 4. Implement `print_trace`

Pretty-print each step:

```
[Step 1] 🔧 Tool: search_web({"query": "population of France"})
         → France has a population of approximately 68 million...

[Step 2] ⛔ Repeat blocked: search_web({"query": "population of France"})

[Step 3] 🔧 Tool: calculator({"expression": "68000000 / 551695"})
         → 123.24...

[Step 4] ✅ Answer: The population density of France is about 123 people per km².
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
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-08-structured-workflows/exercises/01-react-agent
python start.py

# Option B - uv (no activation needed):
cd module-08-structured-workflows/exercises/01-react-agent
uv run python start.py
```

Try queries that require multiple tool calls:
- "What is the population of Japan divided by 1000?"
- "Search for the speed of light and save it in a note"
- "What notes do I have?"

## Tests

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-08-structured-workflows/exercises/01-react-agent
pytest test_start.py -v

# Option B - uv (no activation needed):
cd module-08-structured-workflows/exercises/01-react-agent
uv run --extra dev pytest test_start.py -v
```

The tests check:
- `calculator` returns correct numeric results
- `take_note` / `read_notes` store and retrieve notes
- `TOOL_SCHEMAS` is a non-empty list of tool definitions
- `run_react` returns a dict with `"answer"`, `"trace"` and `"stop_reason"` keys
- **Guard 2**: a repeated tool call never reaches the tool, and is recorded in the trace
- **Guard 2b**: a read repeated *after* a `take_note` is allowed through
- **Guard 3**: exhausting the budget still returns an answer, with `stop_reason="budget_exhausted"`

## Stretch goals

- Add a **cost ceiling**: stop on `response.usage.total_tokens` spent, not just steps taken
- Add a `get_weather(city)` tool using a public API
- Implement a `/history` command that shows the full message list sent to OpenAI
- Track *near*-repeats too: the same tool with trivially different arguments (`"France"` vs `"france "`) is usually the same mistake
