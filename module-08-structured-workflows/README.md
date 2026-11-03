# Module 8 — Structured Workflows

> Every agent you have built so far lets the model decide what happens next. That is a choice, not a default — and usually the most expensive one available. This module is about the spectrum between code-driven and model-driven control flow: fixed chains, routers, plan-and-execute, and ReAct. You will build ReAct properly (with a reasoning trace that is actually populated, and guards that stop it running away), then exploit the thing that makes planning worth it — a plan is **data**, so you can show it, schedule it in parallel, pause it for a human, and resume it after a crash. The module closes Day 2 with a Holiday Planner web app.

## Learning goals

- Place a task on the **control-flow spectrum**: fixed chain, router, plan-and-execute, ReAct.
- Build a **ReAct loop** whose reasoning is visible, with a step budget, repeat detection, and a forced finish.
- Build **plan-and-execute** with re-planning on failure.
- Run independent plan steps **concurrently** with a `depends_on` graph.
- **Pause a plan** for human approval, checkpoint it to disk, and resume without repeating work.

---

## Who owns the control flow?

The question is not "ReAct or planning?". It is **how many decisions am I handing to the model** — because each one is a decision you cannot unit test.

| | Who decides | Cost | Testable | Use when |
|-|-------------|------|----------|----------|
| **Fixed chain** | Your code, entirely | Lowest | Fully | You know the steps |
| **Router** | Model picks a branch | Low | Mostly | A few known shapes of request |
| **Plan-and-execute** | Model decides once, up front | Medium | The plan is inspectable | The task has a shape, but it varies |
| **ReAct** | Model decides every step | Highest | Barely | You cannot know the steps until you see the data |

```python
# Fixed chain: you wrote the order
a = check_system("reactor")
b = check_system("shields")
summarise([a, b])

# ReAct: the model writes the order, one step at a time
while not done:
    step = decide(messages)
    observation = run_tool(step)
```

**The rule: push left.** Start at the top of that table and move down only when the task actually breaks. Moving down buys adaptability and costs tokens, latency, and testability. Most production "agents" are a chain or a router wearing a trench coat, and that is fine. The spectrum is per-task, not per-product — one application can use all four.

---

## ReAct — Reason, Act, Observe

You already built most of this in Module 2: call the model, run the tool, feed the result back. ReAct adds one thing — the model must say **why** before it acts. That reasoning turns a tool log into a trace that explains itself.

### The trap: a Thought that is never there

The obvious implementation reads the thought from `response.output_text`. But with native tool calling, that text is usually **empty** whenever the model emits a `function_call`. So you end up logging a "Thought" field that is blank on every step that actually did something.

The fix is to make the reasoning **structural** rather than hopeful:

```python
class ReActStep(BaseModel):
    thought: str                      # required - cannot come back empty
    action: Literal["check_system", "search_logs", "calculator", "final_answer"]
    action_input: str

response = client.responses.parse(
    model=MODEL, reasoning={"effort": "none"},
    text_format=ReActStep, input=messages,
)
```

The schema, not the prompt, is what guarantees a thought on every turn.

### Three guards

An unguarded loop is the most common way an agent ruins a production afternoon.

```python
seen = set()
for _ in range(max_steps):              # guard 1: step budget
    step = decide(messages, client)

    if step.action == "final_answer":
        return step.action_input

    sig = (step.action, step.action_input)
    if sig in seen:                     # guard 2: no progress
        messages.append(nudge(step))
        continue
    seen.add(sig)

    obs = run_tool(step.action, step.action_input)
    messages += [assistant(step), user(f"Observation: {obs}")]

return force_an_answer(messages)        # guard 3: never return None
```

- **Step budget** bounds the worst case. Without it, cost is unbounded.
- **No-progress detection** catches a model going in circles — a repeated call returns an observation already in the context. But a repeat is only pointless if *nothing changed*: reset the set when a state-mutating tool runs.
- **Forced finalisation** means running out of budget produces a partial answer rather than `None`.

A cost ceiling is the fourth guard: stop on tokens spent, not just steps taken.

---

## Plan-and-execute

ReAct re-decides every turn. Plan-and-execute decides once, up front, and only consults the model again if a step fails.

```python
def plan_and_execute(goal, client, max_replans=1):
    plan = generate_plan(goal, client)
    completed = []

    for i, step in enumerate(plan):
        try:
            step.result = execute_step(step, client)
            step.status = "done"
        except Exception as e:
            step.status = "failed"
            if max_replans > 0:
                plan = completed + revise_plan(plan[i+1:], completed, e, client)
                max_replans -= 1
        completed.append(step)

    return synthesise(goal, completed, client)
```

Cap `max_replans` — re-planning on every failure is an infinite loop with extra steps.

### The real payoff: the plan is data

A ReAct loop lives in a call stack. A plan is a list of objects, which means you can **show it to a user** before anything runs, **store it** and diff intended against actual, **schedule it**, and **stop in the middle of it**. The last two are worth sections of their own.

---

## A plan is a graph, not a list

ReAct picks its next action *after* reading the last observation, so it is serial by construction — even when the work has no ordering constraint. Checking four ship systems has no ordering constraint, but ReAct checks them one at a time.

One extra field turns the list into a schedule:

```python
class PlannedStep(BaseModel):
    number: int
    description: str
    depends_on: list[int]        # empty = nothing is blocking this

def dependency_levels(steps):
    """Group into waves. Everything in a wave can run at once."""
    remaining, done, levels = {s.number: s for s in steps}, set(), []
    while remaining:
        ready = [s for s in remaining.values()
                 if all(d in done or d not in remaining for d in s.depends_on)]
        if not ready:                      # a cycle - do not hang
            levels.append(list(remaining.values()))
            break
        levels.append(ready)
        for s in ready:
            done.add(s.number); del remaining[s.number]
    return levels
```

Then run each wave at once:

```python
for wave in levels:
    results = await asyncio.gather(*(execute_step(s, results, client) for s in wave))
```

Two things to get right. Tell the planner **not to invent dependencies** — models love to impose an order that is not required, and every false dependency costs you a wave. And always handle the cycle case: a confused plan should still run, never deadlock.

---

## Pause, approve, resume

Because the plan is data, you can write it to disk. That buys two properties you cannot retrofit onto ReAct: it survives a restart, and it can block on a human.

```python
NEEDS_APPROVAL = {"file_report", "book_flight", "send_email"}

def run_plan(state):
    approved = set(state.get("approved", []))

    for step in state["steps"]:
        if step["status"] == "done":
            continue                          # resume: never repeat a side effect

        if step["requires_approval"] and step["number"] not in approved:
            step["status"] = "awaiting_approval"
            save_state(state)                 # checkpoint, then stop
            return "awaiting_approval"

        step["result"] = run_tool(step["tool"], step["args"])
        step["status"] = "done"
        save_state(state)                     # checkpoint after every step
    return "complete"
```

**Code decides what is dangerous, not the model.** A plan that marks its own steps as safe is not a safety control — the model is the thing you are guarding against. Keep the irreversible-tool list in code where you can review and test it.

Checkpoint after every step so a crash costs one step rather than the whole run, and make resuming **idempotent** — skipping completed steps is what stops a resume from booking the flight twice.

---

## Summary

- **Push control flow as far left as the task allows.** Chain, router, plan, ReAct — move right only when the task breaks.
- **Make the reasoning structural, not hopeful.** A required `thought` field always arrives; one read off `output_text` usually does not.
- **Every loop needs a budget, a repeat check, and a forced exit.** All three failures are production outages.
- **The plan is data — that is the whole point.** Show it, schedule it in waves, checkpoint it, pause it for a human.

---

## Demos

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python module-08-structured-workflows/demo/demo.py

# Option B - uv (no activation needed):
uv run python module-08-structured-workflows/demo/demo.py
```

`demo.py` is a menu. Each part also runs standalone, for example
`python module-08-structured-workflows/demo/04_parallel_plan.py`.

| Script | What it shows |
| ------ | ------------- |
| `demo/01_control_flow.py` | One task, four strategies — a table of LLM calls, tokens, seconds, and how many decisions the model made |
| `demo/02_react.py` | ReAct with a required `thought` field, plus a stuck model so you can watch the guards fire (no API key needed for that part) |
| `demo/03_plan_and_execute.py` | Plan generation, step execution, re-planning on failure |
| `demo/04_parallel_plan.py` | `depends_on` scheduling into waves, serial vs parallel wall-clock |
| `demo/05_approval_resume.py` | A plan that halts before an irreversible step, checkpoints to JSON, and resumes after approval |

Tools live in `demo/workflow_tools.py`, shared so the four strategies in demo 01 are compared like for like. They sleep briefly to stand in for real network calls; set `DEMO_TOOL_LATENCY=0` to remove the delay.

## Exercises

The four exercises chain together, building up to a complete web application. Each builds on the last; you can bring your own code forward or use the provided solution.

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-react-agent`](exercises/01-react-agent/) | ReAct loop with web search, calculator and notes — full trace, plus a step budget, repeat detection, and a forced finish |
| [`exercises/02-plan-and-execute`](exercises/02-plan-and-execute/) | Planner + executor with re-planning, compared against ReAct |
| [`exercises/03-parallel-approval`](exercises/03-parallel-approval/) | `depends_on` waves run with `asyncio.gather`, an approval gate on irreversible steps, and a JSON checkpoint you can resume from |
| [`exercises/04-holiday-planner`](exercises/04-holiday-planner/) | Holiday Planner web app: FastAPI + Svelte with plan visualisation |

A Svelte + ShadCN + Tailwind frontend is provided in `exercises/04-holiday-planner/frontend/`. Delegates focus on the FastAPI backend.

Run tests per exercise (each folder has its own `test_start.py`):

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pytest module-08-structured-workflows/exercises/01-react-agent/ -v
pytest module-08-structured-workflows/exercises/03-parallel-approval/ -v

# Option B - uv (no activation needed):
uv run --extra dev pytest module-08-structured-workflows/exercises/01-react-agent/ -v
uv run --extra dev pytest module-08-structured-workflows/exercises/03-parallel-approval/ -v
```

## Slides

From repo root: `pnpm slides:08`, or `cd module-08-structured-workflows/slides && pnpm dev`.

## Reference

- [Building Effective Agents (Anthropic, 2024)](https://www.anthropic.com/engineering/building-effective-agents) — the workflows-vs-agents distinction this module is built around
- [ReAct paper (Yao et al. 2023)](https://arxiv.org/abs/2210.03629)
- [Plan-and-Solve (Wang et al. 2023)](https://arxiv.org/abs/2305.04091)
- [LLM Compiler (Kim et al. 2023)](https://arxiv.org/abs/2312.04511) — planning a DAG of tool calls and executing it in parallel
- [LangGraph workflows](https://langchain-ai.github.io/langgraph/) — the typed-state graph this module builds by hand
