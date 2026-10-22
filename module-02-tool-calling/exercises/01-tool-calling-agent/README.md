# Exercise 01 -- Tool-Calling Agent

> Give the Pathfinder AI hands -- define tools the model can call, write the handlers that execute them, and build the loop that ties it all together.

## Recap

So far the model can only talk. To make it **do** things, we give it **tools**. The model does not execute code -- it returns a structured request saying "I want to call this function with these arguments." Your code executes the function, sends the result back, and the model continues.

This introduces two new kinds of conversation item alongside messages: a **`function_call`** (the model's request) and a **`function_call_output`** (your result). A full tool-calling exchange looks like this:

```python
messages = [
    {"role": "system", "content": "You are the Pathfinder AI..."},
    {"role": "user", "content": "How many crew in science?"},
    # Model decides to call a tool:
    {"type": "function_call", "call_id": "call_1",
     "name": "get_crew_count", "arguments": '{"department": "science"}'},
    # You execute the tool and send the result back, matched by call_id:
    {"type": "function_call_output", "call_id": "call_1",
     "output": '{"department": "science", "count": 3}'},
    # Model uses the result to answer:
    {"role": "assistant", "content": "There are 3 crew in the science department."},
]
```

Tools are declared as **JSON Schema** objects that describe the function name, what it does, and what arguments it takes. You pass these to the API alongside the messages:

```python
tools = [
    {
        "type": "function",
        "name": "get_crew_count",
        "description": "Get the number of crew members in a department",
        "parameters": {
            "type": "object",
            "properties": {
                "department": {"type": "string", "description": "Department name"},
            },
            "required": ["department"],
        },
    },
]

response = client.responses.create(
    model=MODEL, reasoning={"effort": "none"}, input=messages, tools=tools,
)
calls = [item for item in response.output if item.type == "function_call"]
```

`response.output` is a list of items. `calls` holds the `function_call` items -- empty if the model chose to answer directly, in which case the text is in `response.output_text`. The **agent loop** pattern is: ask the model, if it wants tools then execute them and ask again, repeat until it gives a text answer or you hit `max_steps`.

This exercise uses the `openai` package.

## What you build

- **`TOOLS`** -- a list of 3 tool schemas (`{"type": "function", "name", "description", "parameters"}`).
- **`get_crew_count(department)`**, **`get_ship_status(system)`**, **`search_crew(query)`** -- handler functions that return JSON strings.
- **`run_agent(client, question, max_steps)`** -- the tool-calling loop. Returns an `AgentResult`.

## Step-by-step

### 1. Define `TOOLS` -- the tool schemas

Add 3 tool definitions to the `TOOLS` list. Each follows this structure:

```python
{
    "type": "function",
    "name": "get_crew_count",
    "description": "Get the number of crew members in a department",
    "parameters": {
        "type": "object",
        "properties": {
            "department": {"type": "string", "description": "Department name"},
        },
        "required": ["department"],
    },
}
```

Define all three: `get_crew_count` (takes `department`), `get_ship_status` (takes `system`), and `search_crew` (takes `query`). The descriptions help the model decide which tool to use, so be clear.

### 2. Implement the handler functions

Each handler takes its arguments and returns a **JSON string**:

- **`get_crew_count(department)`** -- look up `CREW_DATA.get(department, [])`, return `json.dumps({"department": department, "count": len(crew)})`.
- **`get_ship_status(system)`** -- look up `SHIP_SYSTEMS.get(system, {"system": system, "status": "unknown"})`, return `json.dumps(status)`.
- **`search_crew(query)`** -- iterate over all departments in `CREW_DATA`, match crew where `query.lower()` appears in the name or role (case-insensitive), return `json.dumps(matches)`.

The tests call these functions directly and check the JSON output.

### 3. Implement `run_agent(client, question, max_steps) -> AgentResult`

This is the core loop:

1. Build the messages list: `[system_msg, {"role": "user", "content": question}]`.
2. Track `tool_calls_made` (list of tool names) and `steps` (counter).
3. Loop up to `max_steps` times:
   - Call `client.responses.create(model=MODEL, reasoning={"effort": "none"}, input=messages, tools=TOOLS)`.
   - Collect the tool calls: `calls = [item for item in response.output if item.type == "function_call"]`.
   - If `calls` is not empty:
     - Add the model's output to the history: `messages += response.output`.
     - For each call `tc`: parse the arguments with `json.loads(tc.arguments)`, call the handler from `TOOL_HANDLERS[tc.name]`, and append `{"type": "function_call_output", "call_id": tc.call_id, "output": result}`.
     - Record the tool name in `tool_calls_made`.
   - Else if `response.output_text` is not empty: return an `AgentResult` with the answer.
   - Else: break (unexpected state).
4. If you exhaust `max_steps`, return `AgentResult(final_answer=None, ...)`.

The `max_steps` cap is critical -- without it, a confused model can loop forever.

## Try it

```bash
python start.py
```

Try these questions:

- `"How many crew in the science department?"` -- should call `get_crew_count` and answer "3".
- `"What's the status of the sensors?"` -- should call `get_ship_status` and report "degraded".
- `"Find all engineers"` -- should call `search_crew` and list the engineering crew.
- `"Who is Voss and what's the warp status?"` -- may call multiple tools in one turn.

## Tests

```bash
pytest module-02-tool-calling/exercises/01-tool-calling-agent/test_start.py -v
```

## Stretch goals

1. Add a fourth tool like `list_departments()` that returns all department names.
2. Try changing the system prompt to make the agent respond in a different style (e.g. formal report format).
