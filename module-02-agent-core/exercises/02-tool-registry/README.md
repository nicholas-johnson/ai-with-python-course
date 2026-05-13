# Exercise 02 -- Tool Registry

> Replace hand-written JSON schemas with a decorator-based tool registry that auto-generates the OpenAI tool list, routes calls, and handles errors.

## Recap

In Exercise 01 you defined tools as raw JSON dicts and routed calls with a manual `TOOL_HANDLERS` dictionary. That works, but it is tedious and error-prone -- the schema and the handler are in different places, so they can drift out of sync.

A **tool registry** solves this by keeping the schema next to the handler using a **decorator**:

```python
registry = ToolRegistry()

@registry.register("ship_status", "Get current status of a ship system", {
    "type": "object",
    "properties": {"system": {"type": "string"}},
    "required": ["system"],
})
def ship_status(system: str) -> str:
    return json.dumps({"system": system, "status": "online"})
```

The decorator stores the function alongside its metadata. The registry then provides two methods:

- **`list_tools()`** -- returns the full OpenAI-compatible tool list, ready to pass to the API.
- **`execute(name, arguments)`** -- looks up the tool, calls the handler with `**arguments`, catches exceptions, and returns a string result.

This pattern is how production agent frameworks work. The registry is the single source of truth for what the agent can do.

This exercise builds on Exercise 01. The agent loop and ship data are provided from the Exercise 01 solution. You only need to implement the `ToolRegistry` class and register the tools.

## What you build

- **`ToolRegistry`** class with `register()`, `list_tools()`, and `execute()`.
- Three tool registrations using the `@registry.register(...)` decorator.

The agent loop in `run_agent()` is already provided and uses `registry.list_tools()` and `registry.execute()`.

## Step-by-step

### 1. Implement `register(name, description, parameters)` -- the decorator

This method should return a **decorator function** that:

1. Stores the tool info in `self._tools[name]` -- save the name, description, parameters, and the handler function.
2. Returns the original function unchanged (so it can still be called directly).

The pattern:

```python
def register(self, name, description, parameters):
    def decorator(fn):
        self._tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": fn,
        }
        return fn
    return decorator
```

The tests check that after registering, `self._tools` contains the tool.

### 2. Implement `list_tools() -> list[dict]`

Build and return a list in OpenAI format by iterating over `self._tools.values()`:

```python
[
    {
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t["description"],
            "parameters": t["parameters"],
        },
    }
    for t in self._tools.values()
]
```

The tests check that the returned list has the right length and correct structure.

### 3. Implement `execute(name, arguments) -> str`

Look up the tool and call its handler:

1. If `name` is not in `self._tools`, return `json.dumps({"error": f"Unknown tool: {name}"})`.
2. Otherwise, call `self._tools[name]["handler"](**arguments)`.
3. If the handler returns a string, return it directly. Otherwise, `json.dumps()` the result.
4. Wrap the call in a `try/except` -- if the handler raises, return `json.dumps({"error": f"Tool error: {exc}"})`.

The tests check the happy path, unknown-tool error, and exception handling.

### 4. Register the three tools

Use `@registry.register(...)` to register `get_crew_count`, `get_ship_status`, and `search_crew`. The implementations are the same as Exercise 01 -- look up data from `CREW_DATA` and `SHIP_SYSTEMS` and return JSON strings. The example in the comments shows the decorator syntax.

## Try it

```bash
python start.py
```

The agent behaves identically to Exercise 01, but the code is cleaner. On startup it prints the registered tool names -- if you see "WARNING: No tools registered!" you need to implement the decorator and registrations first.

Try the same questions:

- `"How many crew in engineering?"` -- should call `get_crew_count`.
- `"What's the sensor status?"` -- should call `get_ship_status`.
- `"Find Captain Voss"` -- should call `search_crew`.

## Tests

```bash
pytest module-02-agent-core/exercises/02-tool-registry/test_start.py -v
```

## Stretch goals

1. Add a `list_tool_names()` method that returns just the tool names as a list of strings.
2. Add argument validation in `execute()` -- check that required fields from the schema are present before calling the handler.
