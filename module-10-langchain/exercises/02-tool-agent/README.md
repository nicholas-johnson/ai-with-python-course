# Exercise 2: Tool Agent

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

**`AgentExecutor`** — runs the tool-calling loop. You create an agent from a model + tools + prompt, then the executor handles: LLM call → tool dispatch → feed result back → repeat until the model answers directly.

```python
from langchain.agents import create_tool_calling_agent, AgentExecutor

agent = create_tool_calling_agent(model, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
result = executor.invoke({"input": "What is the reactor temperature?"})
```

`verbose=True` prints the full thought/action/observation trace — the same pattern you built by hand.

## What you build

A console agent in **`start.py`** that uses LangChain tools to classify reports (from Exercise 1), read sensor data, and query the crew roster.

The Exercise 1 classifier chain is already inlined at the top of `start.py` — you'll add tools and the agent below it.

**Key functions:**

| Function | Description |
|---|---|
| `run_agent(query)` | Invoke the agent executor, return the response string |

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
    "hull_temperature": {"value": 272, "unit": "K", "status": "nominal"},
    "reactor_output": {"value": 94.2, "unit": "%", "status": "nominal"},
    "shield_integrity": {"value": 87, "unit": "%", "status": "warning"},
    "oxygen_level": {"value": 21.1, "unit": "%", "status": "nominal"},
    "radiation": {"value": 0.3, "unit": "mSv/h", "status": "nominal"},
}
```

Load crew data from `data/crew.json` at the project root.

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

Create a prompt, model, and agent:

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are the DSS Pathfinder AI assistant. Use your tools to help the crew."),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
agent = create_tool_calling_agent(model, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
```

The `{agent_scratchpad}` placeholder is where LangChain inserts tool call/result pairs during the loop.

### 5. Implement `run_agent`

```python
def run_agent(query: str) -> str:
    result = executor.invoke({"input": query})
    return result["output"]
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

Try queries that require tools: "What is the shield integrity?", "Classify this report: Warp core fluctuations detected", "Who is in the engineering department?"

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
