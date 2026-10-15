# Exercise 2: Tool Agent

> **Scenario:** Hands-on work uses the **CSS Horizon** and `module-10-langchain/exercises/data/horizon_crew.json`. Module demos use the **DSS Pathfinder** and `data/crew.json` at the repo root.

## Recap

In Module 2 you built a tool-calling agent loop by hand — the LLM decides whether to respond or call a tool, you execute the tool, feed the result back, and repeat. LangChain wraps this entire loop in two components:

**`@tool` decorator** — turns any Python function into a LangChain tool. The JSON Schema is generated from the type hints and docstring:

```python
from langchain_core.tools import tool

@tool
def read_sensor(sensor_name: str) -> str:
    """Read the current value of a ship sensor."""
    return json.dumps(SENSOR_DATA.get(sensor_name, {"error": "Unknown sensor"}))
```

**`create_agent`** — runs the tool-calling loop. You give it a model, tools, and a system prompt; it handles: LLM call → tool dispatch → feed result back → repeat until the model answers directly. Under the hood it is a LangGraph graph.

```python
from langchain.agents import create_agent

agent = create_agent(model, tools, system_prompt="You are the CSS Horizon AI assistant.")
result = agent.invoke({"messages": [{"role": "user", "content": "What is the reactor temperature?"}]})
answer = result["messages"][-1].text
```

`result["messages"]` holds every step — the user message, each tool call, each tool result, and the final answer — the same pattern you built by hand.

## What you build

A console agent in **`start.py`** that uses LangChain tools to classify reports (from Exercise 1), read sensor data, and query the crew roster.

The Exercise 1 classifier chain is already inlined at the top of `start.py` — you'll add tools and the agent below it.

**Key functions:**

| Function | Description |
|---|---|
| `run_agent(query)` | Invoke the agent, return the final answer string |

**Tools the agent can call:**

| Tool | What it does |
|---|---|
| `classify_report` | Classify a crew report (from Exercise 1) |
| `read_sensor` | Read a ship sensor by name |
| `query_crew` | Look up crew members by department |

## Step-by-step

### 1. Review the inlined classifier

The Exercise 1 solution (classifier chain + `classify_report()`) is already at the top of `start.py`. You don't need to change it — just use `classify_report()` in your tools below.

### 2. Define sensor and crew data

Define inline data for the agent's tools:

```python
SENSOR_DATA = {
    "cargo_hold_pressure": {"value": 101.2, "unit": "kPa", "status": "nominal"},
    "main_drive_output": {"value": 96.0, "unit": "%", "status": "nominal"},
    "docking_seal_integrity": {"value": 94.0, "unit": "%", "status": "nominal"},
    "life_support_o2": {"value": 20.9, "unit": "%", "status": "nominal"},
    "background_radiation": {"value": 0.12, "unit": "mSv/h", "status": "nominal"},
}
```

Load crew data from `module-10-langchain/exercises/data/horizon_crew.json`:

```python
EXERCISE_DATA = Path(__file__).resolve().parents[1] / "data"
CREW = json.loads((EXERCISE_DATA / "horizon_crew.json").read_text())
```

### 3. Create `@tool` functions

Wrap each capability as a LangChain tool:

```python
@tool
def classify(report: str) -> str:
    """Classify a crew report into category, summary, and priority."""
    result = classify_report(report)
    return json.dumps(result)

@tool
def read_sensor(sensor_name: str) -> str:
    """Read the current value of a ship sensor."""
    ...

@tool
def query_crew(department: str) -> str:
    """Look up crew members by department."""
    ...
```

**Important:** LangChain tools must return strings. Wrap dicts in `json.dumps()`.

### 4. Build the agent

Create a system prompt, model, and agent:

```python
SYSTEM_PROMPT = "You are the CSS Horizon AI assistant. Use your tools to help the crew."

model = ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0)
agent = create_agent(model, tools, system_prompt=SYSTEM_PROMPT)
```

There is no prompt template with an `{agent_scratchpad}` any more — the agent keeps tool calls and results in its `messages` state.

### 5. Implement `run_agent`

```python
def run_agent(query: str) -> str:
    result = agent.invoke({"messages": [{"role": "user", "content": query}]})
    return result["messages"][-1].text
```

### 6. Build the interactive loop

Handle these commands:

| Command | Action |
|---|---|
| any text | Send to the agent, print the response |
| `/tools` | List all available tools with descriptions |
| `/sensors` | List available sensor names |
| `quit` | Exit |

## Try it

```bash
cd module-10-langchain/exercises/02-tool-agent
python start.py
```

Try queries that require tools: "What is the docking seal integrity?", "Classify this report: Cargo hold pressure dropped during sample loading", "Who is in the engineering department?"

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- `run_agent` returns a non-empty string

## Stretch goals

- Add a `log_query` tool that searches ship logs by keyword
- Add conversation memory so the agent remembers previous questions
- Toggle `verbose` on/off with a `/verbose` command
