# Exercise 02 -- Auto-Schema Tool Registry

> Build a tool registry that auto-generates OpenAI-compatible JSON schemas from Python type hints, then wire it into a planetary exploration agent.

## Recap

In Exercise 01 you defined tools as raw JSON dicts and routed calls with a manual `TOOL_HANDLERS` dictionary. That works, but keeping the JSON schema in sync with the Python function signature is tedious and error-prone.

Production frameworks solve this with **introspection** -- they look at the function's type hints and build the schema automatically. In this exercise you will build a registry that does the same thing.

Instead of this (from the demo):

```python
@registry.register("scan_planet", "Scan a planet", {
    "type": "object",
    "properties": {"planet_id": {"type": "string"}},
    "required": ["planet_id"],
})
def scan_planet(planet_id: str) -> str: ...
```

You will write this:

```python
@registry.register("Scan a planet by its catalog ID")
def scan_planet(planet_id: str) -> str: ...
```

The registry reads `inspect.signature(fn)` to discover parameter names and types, then maps them to JSON Schema types using a simple lookup:

| Python type | JSON Schema type |
|-------------|-----------------|
| `str`       | `"string"`      |
| `int`       | `"integer"`     |
| `float`     | `"number"`      |
| `bool`      | `"boolean"`     |

Parameters without a default value are marked as `"required"`.

## What you build

- **`ToolRegistry`** class with `register(description)`, `list_tools()`, and `execute()`.
- Three planetary exploration tools registered with `@registry.register(...)`.

The agent loop in `run_agent()` is already provided and uses `registry.list_tools()` and `registry.execute()`.

## Step-by-step

### 1. Implement `register(description)` -- the auto-schema decorator

This method takes only a description string and returns a decorator. Inside the decorator:

1. Call `inspect.signature(fn)` to get the function's parameters.
2. For each parameter, look up `param.annotation` in `TYPE_MAP` to get the JSON Schema type.
3. Parameters where `param.default is inspect.Parameter.empty` are required.
4. Store the tool in `self._tools[fn.__name__]` with the name, description, auto-generated schema, and handler.
5. Return `fn` unchanged.

```python
def register(self, description: str):
    def decorator(fn):
        sig = inspect.signature(fn)
        properties = {}
        required = []
        for param_name, param in sig.parameters.items():
            json_type = TYPE_MAP.get(param.annotation, "string")
            properties[param_name] = {"type": json_type}
            if param.default is inspect.Parameter.empty:
                required.append(param_name)
        self._tools[fn.__name__] = { ... }
        return fn
    return decorator
```

### 2. Implement `list_tools() -> list[dict]`

Same as the demo -- iterate `self._tools.values()` and build the OpenAI format:

```python
[{"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}]
```

### 3. Implement `execute(name, arguments) -> str`

Same error-handling pattern as the demo:

1. Unknown tool -> return `{"error": "Unknown tool: <name>"}`.
2. Call `handler(**arguments)`. If the result is a string, return it; otherwise `json.dumps()` it.
3. Wrap in `try/except` -- if the handler raises, return `{"error": "Tool error: <message>"}`.

### 4. Register the three planetary tools

Use `@registry.register(description)` to register:

- **`scan_planet(planet_id: str)`** -- look up the planet in `PLANET_DB`, return its data as JSON.
- **`check_habitability(atmosphere: str, gravity: float)`** -- score habitability based on atmosphere type and gravity range.
- **`log_discovery(planet_id: str, summary: str)`** -- append an entry to `MISSION_LOG`.

The tool implementations are described in the comments in `start.py`.

## Try it

```bash
python start.py
```

The agent uses your registry to explore planets. Try these:

- `"Scan planet KEP-442b"` -- should call `scan_planet`.
- `"Is TRAP-1e habitable?"` -- should call `scan_planet`, then `check_habitability`.
- `"Log that PROX-b has high radiation"` -- should call `log_discovery`.

## Tests

```bash
pytest test_start.py -v
```

## Stretch goals

1. Add support for `list[str]` parameters (map to `{"type": "array", "items": {"type": "string"}}`).
2. Use `Annotated[str, "Planet catalog ID"]` to pull per-parameter descriptions into the schema.
