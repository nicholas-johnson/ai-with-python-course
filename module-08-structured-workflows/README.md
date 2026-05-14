# Module 8 — Structured Workflows

> So far our agents respond to each message independently — they can call tools, but they don't plan ahead or show their reasoning. Structured workflows change that. This module introduces two patterns that give agents deliberate, traceable behaviour: **ReAct** (Reason → Act → Observe) for step-by-step exploration, and **plan-and-execute** for multi-step tasks with upfront planning. The module closes Day 2 with a Holiday Planner web app that puts both patterns to work.

## Learning goals

- Build a **ReAct loop** with explicit Thought → Action → Observation traces.
- Build a **plan-and-execute** workflow that generates a plan, executes steps, and re-plans on failure.
- Compare both patterns: when to use which, and the trade-offs in cost, latency, and reliability.
- Integrate workflows into a **web application** with streaming and plan visualisation.

---

## ReAct — Reason, Act, Observe

ReAct is a structured workflow where the agent explicitly reasons before acting. Each step has three phases:

1. **Thought** — the agent writes its reasoning (visible in logs, not shown to the user).
2. **Action** — the agent calls a tool.
3. **Observation** — the tool result is appended to the context.

The loop repeats until the agent's thought concludes with a final answer.

```python
def run_react(query, tools, client, max_steps=10):
    messages = [system_prompt, {"role": "user", "content": query}]
    trace = []
    for _ in range(max_steps):
        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages,
            tools=tool_schemas, tool_choice="auto",
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            return {"answer": msg.content, "trace": trace}

        for tc in msg.tool_calls:
            result = tools[tc.function.name](**json.loads(tc.function.arguments))
            trace.append({"tool": tc.function.name, "result": result})
            messages.append({"role": "tool", "content": result, "tool_call_id": tc.id})

    return {"answer": None, "trace": trace}
```

The trace is invaluable for debugging — you can see exactly why the agent made each decision. Log it in production.

---

## Plan-and-execute

ReAct decides one step at a time. Plan-and-execute takes a different approach: generate a complete plan first, then execute each step.

```
1. [Plan] Search for destination options
2. [Plan] Compare prices and reviews
3. [Plan] Check available flights
4. [Plan] Book the best option
```

The planner generates the full sequence. The executor runs each step, collecting results. If a step fails, the planner can revise the remaining steps.

| | ReAct | Plan-and-execute |
|-|-------|-----------------|
| Planning | One step at a time | Full plan up front |
| Adaptability | Highly reactive | Revises on failure |
| Traceability | Per-step thought logs | Full plan visible |
| Token cost | Lower per step | Higher for planning |
| Best for | Exploratory queries | Structured multi-step tasks |

---

## Field rules

- **Cap your loops.** ReAct max_steps and plan-and-execute max_replans prevent runaway agents.
- **Log the trace.** Thoughts + actions + observations are your best debugging tool.
- **Choose the right pattern.** ReAct for exploration, plan-and-execute for structured tasks.
- **Show the plan to the user.** Transparency builds trust — let users see what the agent intends to do.

---

## Demos

```bash
python module-08-structured-workflows/demo/01_react.py
python module-08-structured-workflows/demo/02_plan_and_execute.py
```

| Script | What it shows |
| ------ | ------------- |
| `demo/01_react.py` | ReAct loop with real tools — Thought/Action/Observation trace printed live |
| `demo/02_plan_and_execute.py` | Plan generation, step-by-step execution, re-planning on failure |

## Exercises

The three exercises chain together, building up to a complete web application. Each builds on the last; you can bring your own code forward or use the provided solution.

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-react-agent`](exercises/01-react-agent/) | Build a ReAct loop with web search, calculator, and notes — full trace output |
| [`exercises/02-plan-and-execute`](exercises/02-plan-and-execute/) | Planner + executor with re-planning, compare ReAct vs plan-and-execute |
| [`exercises/03-holiday-planner`](exercises/03-holiday-planner/) | Holiday Planner web app: FastAPI + Svelte with plan visualisation |

A Svelte + ShadCN + Tailwind frontend is provided in `exercises/03-holiday-planner/frontend/`. Delegates focus on the FastAPI backend.

Run tests for this module:

```bash
pytest module-08-structured-workflows/
```

## Slides

From repo root: `pnpm slides:08`, or `cd module-08-structured-workflows/slides && pnpm dev`.

## Reference

- [ReAct paper (Yao et al. 2023)](https://arxiv.org/abs/2210.03629)
- [Plan-and-Solve (Wang et al. 2023)](https://arxiv.org/abs/2305.04091)
- [LangGraph workflows](https://langchain-ai.github.io/langgraph/)
