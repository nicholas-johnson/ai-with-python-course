# Exercise 03 — Parallel Plans and Approval Gates

## Recap

Exercise 02 produced a plan and ran it top to bottom. That is already better than ReAct in one important way: the plan exists as **data** before anything happens.

This exercise cashes in on that. Two capabilities fall out of having the plan written down, and **neither is available to a ReAct loop at all**:

**1. Independent steps can run at the same time.** ReAct chooses its next action *after* reading the last observation, so it is serial by construction — even when the work has no ordering constraint at all. Researching four cities has no ordering constraint. A plan can say so.

**2. The workflow can stop in the middle.** A ReAct loop lives in a Python call stack: kill the process and the work is gone, and there is no moment where a human can step in before something irreversible happens. A plan on disk can pause, wait for a human, survive a restart, and carry on.

```
Goal: compare Lisbon, Palermo and Tallinn, then book the cheapest

  wave 1  ──┬── 1. research Lisbon      ⎫
            ├── 2. research Palermo     ⎬ no dependencies, so all at once
            └── 3. research Tallinn     ⎭
  wave 2  ───── 4. compare costs          (depends on 1, 2, 3)
  wave 3  ───── 5. find the flight        (depends on 4)
  wave 4  ───── 6. book it            ⛔  needs human approval
```

## What you build

A console app in **`start.py`** that plans, schedules, gates, and checkpoints.

`tools.py` is **provided** — it has the tools (`research_destination`, `find_flight`, `book_flight`, `calculator`, `take_note`, `search_web`), the `IRREVERSIBLE` set, and an async `execute_step` that runs a single step as a small tool-calling agent. You do not need to change it.

| Function | Description |
|---|---|
| `generate_plan(goal, client)` | Plan with `depends_on`, then set `requires_approval` **in code** |
| `dependency_levels(steps)` | Group steps into waves that can run concurrently |
| `save_state` / `load_state` / `approve` | Persist the plan to JSON and record approvals |
| `run_plan(goal, steps, approved, client)` | Run wave by wave, stop at a gate, skip finished steps |

## Step-by-step

### 1. Extend the plan schema

`PlannedStep` is what the model returns; `PlanStep` is the runtime object. The model supplies `depends_on`, but it must **not** supply `requires_approval`:

```python
class PlannedStep(BaseModel):
    step_number: int
    description: str
    tool: str
    depends_on: list[int]      # empty = nothing is blocking this step
```

In `generate_plan`, set the gate yourself:

```python
requires_approval = step.tool in IRREVERSIBLE
```

> **Why code and not the model?** Because a plan that can mark its own steps as safe is not a safety control. The model is the thing you are guarding against. Keep the dangerous-tool list in code, where you can review it and test it.

Prompting matters here too: tell the planner explicitly that independent steps must have an empty `depends_on`. Models love to invent a sequential order that is not actually required, and every false dependency costs you a wave.

### 2. Implement `dependency_levels`

Repeatedly take every step whose dependencies are already satisfied, emit them as one wave, and mark them done:

```python
remaining = {s.step_number: s for s in steps}
done, levels = set(), []
while remaining:
    ready = [s for s in remaining.values()
             if all(d in done or d not in remaining for d in s.depends_on)]
    ...
```

Two cases to get right:

- A dependency that is **not in `remaining`** counts as satisfied — it either finished already or the model referenced a step that does not exist.
- If **nothing is ready**, the plan has a cycle. Emit the remainder as one final wave and break. A confused plan should still run; it must never hang.

### 3. Implement the checkpoint

`save_state` writes `{"goal": ..., "steps": [...], "approved": [...]}` as JSON. Use `dataclasses.asdict` on the way out and `PlanStep(**s)` on the way back, so `status` and `result` survive the round trip.

Save **after every wave**, not just at the end. A crash should cost you one wave, not the whole run.

### 4. Implement `run_plan`

```python
for wave in dependency_levels(steps):
    pending = [s for s in wave if s.status != "done"]     # resume safely
    # if any pending step is gated and unapproved -> save and return
    results = await asyncio.gather(
        *(execute_step(s.description, _context_for(s, steps), client) for s in pending)
    )
```

Three requirements:

1. **Skip finished steps.** This single line is what makes `run_plan` safe to call repeatedly. Without it, resuming books the flight twice.
2. **Stop at the gate before running anything in that wave.** Set the step's status to `awaiting_approval`, save, and return `"awaiting_approval"`.
3. **`asyncio.gather` the wave**, not a `for` loop with `await` inside it. An `await` in a loop is just a slow serial loop.

### 5. Try the CLI

| Command | Action |
|---|---|
| `/plan <goal>` | Generate a plan and show its waves |
| `/run` | Run until complete or blocked |
| `/approve N` | Approve step N |
| `/state` | Print the raw checkpoint JSON |
| `/reset` | Delete the checkpoint and start over |

## Try it

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-08-structured-workflows/exercises/03-parallel-approval
python start.py

# Option B - uv (no activation needed):
cd module-08-structured-workflows/exercises/03-parallel-approval
uv run python start.py
```

A session worth walking through:

```
> /plan Compare Lisbon, Palermo and Tallinn for a May trip, then book the cheapest flight
> /run                 # runs the research steps concurrently, stops before booking
> /state               # the plan is on disk, mid-flight
> quit                 # kill the process entirely
> python start.py      # it comes back exactly where it was
> /approve 6
> /run                 # books, and does not redo the research
```

## Tests

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-08-structured-workflows/exercises/03-parallel-approval
pytest test_start.py -v

# Option B - uv (no activation needed):
cd module-08-structured-workflows/exercises/03-parallel-approval
uv run --extra dev pytest test_start.py -v
```

The tests check:
- `PlanStep` carries `depends_on` and `requires_approval` alongside runtime state
- `generate_plan` gates `book_flight` from `IRREVERSIBLE`, and keeps `depends_on`
- `dependency_levels` groups independent steps into one wave, respects real dependencies, and does not hang on a cycle
- `run_plan` blocks before an unapproved gated step and does not execute it
- Resuming after approval skips completed steps and runs the gated one exactly once
- A wave of three 0.2s steps finishes in well under 0.5s — a serial implementation fails this
- The checkpoint round-trips through JSON with statuses and results intact

## Stretch goals

- Add a **budget gate**: require approval for any booking over a threshold, rather than for every booking
- Let a failed step re-plan only its own subtree, leaving unrelated waves untouched
- Add a `/why N` command that prints why step N is in the wave it is in
- Add a timeout per wave, so one slow step cannot stall the whole plan
