# Exercise 02 — Plan-and-Execute

## Recap

ReAct works great for short tasks (2–5 tool calls), but for complex multi-step problems it can lose its way — the model forgets earlier reasoning, repeats work, or never converges.

**Plan-and-Execute** separates the *thinking* from the *doing*:

1. **Plan** — an LLM generates a numbered list of steps to solve the problem
2. **Execute** — each step is handed to a ReAct agent that focuses on that one sub-task
3. **Revise** — if a step fails or produces unexpected results, the LLM revises the remaining plan

This separation brings several advantages:
- The planner can reason about the big picture without tool-calling distractions
- Each execution step is focused and short, staying within ReAct's sweet spot
- Failed steps can be recovered from by replanning

```
User query
    │
    ▼
┌─────────┐     ┌───────────┐     ┌───────────┐
│  Plan    │────▶│  Execute  │────▶│  Revise   │──┐
│ (LLM)   │     │  (ReAct)  │     │  (LLM)    │  │
└─────────┘     └───────────┘     └───────────┘  │
    ▲                                              │
    └──────────────────────────────────────────────┘
                    (if steps remain)
```

## What you build

A console app in **`start.py`** that orchestrates a plan-and-execute workflow. It imports the ReAct agent from Exercise 01 (`react_agent.py`, provided) and layers planning on top.

**Key functions:**

| Function | Description |
|---|---|
| `generate_plan(query, client)` | Ask the LLM to create a numbered plan as JSON |
| `execute_step(step, context, client)` | Use ReAct to execute a single plan step |
| `revise_plan(plan, results, query, client)` | Ask the LLM to revise remaining steps |
| `plan_and_execute(query, client)` | Full orchestration: plan → execute → revise loop |

## Step-by-step

### 1. Understand the data structures

`PlanStep` is a dataclass:

```python
@dataclass
class PlanStep:
    step_number: int
    description: str
    status: str = "pending"     # pending | running | done | failed
    result: str = ""
```

### 2. Implement `generate_plan`

Call `gpt-4o-mini` with `response_format={"type": "json_object"}` and a system prompt asking for a JSON object like:

```json
{
    "steps": [
        {"step_number": 1, "description": "Search for the population of France"},
        {"step_number": 2, "description": "Search for the area of France in km²"},
        {"step_number": 3, "description": "Calculate population density"}
    ]
}
```

Parse the response and return a list of `PlanStep` objects.

### 3. Implement `execute_step`

Build a query string that includes:
- The step description
- Any context from previous steps (so the ReAct agent has what it needs)

Pass it to `run_react` from `react_agent` and return the result.

### 4. Implement `revise_plan`

When a step fails, send the LLM:
- The original query
- Steps completed so far (with their results)
- The failed step
- Remaining steps

Ask it to return a revised list of remaining steps as JSON. Parse into `PlanStep` objects.

### 5. Implement `plan_and_execute`

Orchestrate everything:

1. Call `generate_plan` to get the initial plan
2. Print the plan
3. For each step:
   - Set status to `"running"`, print it
   - Call `execute_step`
   - If it succeeds, set status to `"done"`, store the result
   - If it fails, call `revise_plan` to get new remaining steps
4. After all steps complete, compile results and return a final answer

### 6. Build the interactive loop

| Command | Action |
|---|---|
| any text | Run plan-and-execute, show plan + step-by-step execution |
| `/plan` | Re-display the last generated plan |
| `/react <query>` | Run the same query with pure ReAct (for comparison) |
| `/replan` | Force re-plan of the last query |
| `quit` | Exit |

## Try it

```bash
cd module-08-structured-workflows/exercises/02-plan-and-execute
python start.py
```

Try complex queries that benefit from planning:
- "Compare the populations of France and Germany, then calculate which has higher population density"
- "Find the speed of light, convert it to miles per hour, and save the result as a note"
- "Research three facts about Mars and summarize them"

Then compare with `/react <same query>` to see the difference.

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- `PlanStep` dataclass has the required fields
- `generate_plan` returns a list of `PlanStep` (mocked OpenAI)
- `execute_step` returns a result dict
- `plan_and_execute` returns a dict with `"answer"` and `"plan"` keys

## Stretch goals

- Add a `/compare <query>` command that runs both ReAct and Plan-and-Execute and compares token usage
- Implement parallel execution of independent steps
- Add a `/verbose` toggle that shows the full ReAct trace for each step
