# Exercise 05 — Spawned Subagents

## Recap

Exercises 01–04 all share one roster of agents, fixed in the source: a router picks one of three, a supervisor calls the same critic every time, a swarm hands control sideways between three officers who were there at import time.

A **subagent** is different. The lead creates it on demand, hands it one brief, and gets back one report. The child runs in **its own context window** — it never sees the lead's conversation, and the lead never sees the child's tool calls. That isolation is the real reason to spawn: a researcher can burn thirty archive reads and the lead still only pays for the summary.

```
                      ┌── medical    (own context, own archive) ──┐
Question → Lead agent ├── logistics  (own context, own archive) ──┤ → reconcile → merge → answer
                      └── tactical   (own context, own archive) ──┘
```

Three ideas, in order:

1. **Fan-out** — independent briefs run concurrently, capped, and one failure does not sink the rest.
2. **Spawning as a tool** — the lead gets `spawn_researchers(briefs=[...])`, so *the model* decides how many children to create and what each one is asked.
3. **Fan-in** — reports come back disagreeing, and you have to notice before you paste them into a merge prompt.

## What you build

A console app in **`start.py`** where a lead agent researches a rescue decision by spawning subagents across three departments, then merges what comes back.

**Provided:** [`tools.py`](tools.py) — mock department archives, `read_archive`, `ARCHIVE_TOOL`, `SPAWN_TOOL`, the prompts, and the data shapes (`Brief`, `SubagentReport`, `Finding`, `Reconciled`).

The archives contain a **deliberate disagreement**: logistics reads the rescue window as about 8 hours, tactical as about 3. Your `reconcile` has to catch it.

**Key functions:**

| Function | Description |
|---|---|
| `build_task_brief` | Role prompt + the one task, and nothing else |
| `run_subagent` | One subagent: scoped tool loop, structured report out |
| `fan_out` | All briefs at once, capped by a semaphore, failures contained |
| `handle_spawn_calls` | Run every brief the lead asked for in a turn concurrently |
| `reconcile` | Deterministic pass: duplicates, conflicting numbers, low confidence |
| `synthesise` | One merge call, told what code already found |
| `lead_loop` | Lead turn → spawn → reconcile → merge |

Everything is `async` — fan-out is the whole point, and you cannot do it from blocking calls. `run_serial` and `run_fixed_briefs` are provided so you can time the difference.

## Step-by-step

### 1. Implement `build_task_brief`

Look up `SUBAGENT_PROMPTS[department]` and return a system message plus a user message with the task. Two messages, no more — the subagent gets no history to lean on, so the brief must stand alone.

### 2. Implement `run_subagent`

A tool loop, like Module 2's, but ending in a structured report:

- `await client.responses.parse(...)` with `model=MODEL`, `reasoning={"effort": "none"}`, `input=messages`, `tools=[ARCHIVE_TOOL]`, `tool_choice="auto"`, `text_format=SubagentReport`
- No `function_call` items in `response.output` means it filed its report — wrap `response.output_parsed` in a `Finding`
- Otherwise extend `messages` with `response.output`, `await read_archive(brief.department, query)` for each call, and append `{"type": "function_call_output", "call_id": ..., "output": observation}`
- Track `raw_chars` as you go: everything the subagent read. That number versus the size of its report is the context saving, and the REPL prints it

### 3. Implement `fan_out`

```python
limit = asyncio.Semaphore(max_workers)

async def guarded(brief):
    async with limit:
        return await run_subagent(brief, client)

settled = await asyncio.gather(*(guarded(b) for b in briefs), return_exceptions=True)
```

Then turn `settled` into findings. Two rules:

- **`return_exceptions=True`** — without it, one subagent raising cancels the siblings and you lose work that already finished.
- **Return a list that lines up with `briefs`.** Substitute a stub report for a failure rather than dropping it, so the caller can still match finding *i* to tool call *i*.

### 4. Implement `handle_spawn_calls`

`spawn_researchers` takes a **list** of briefs, and the lead may make more than one call in a turn. Parse each call's `briefs` into `Brief` objects with `_to_brief`, keep track of which group came from which `call_id`, then run **one** `fan_out` over all of them and slice the reports back per call.

One fan-out per turn, not one per call — otherwise two calls in the same turn run one after the other and you have lost the concurrency you were after.

Why a list rather than one brief per call? Models are supposed to emit several tool calls in a turn when the work is independent, but plenty of them reliably do not: they spawn one, read the report, then spawn the next, and your parallel system quietly runs serially. Making the batch an *argument* means the fan-out shape is committed in one decision you can see.

The lead gets the reports. It does not get the transcripts.

### 5. Implement `reconcile`

A plain function, no LLM:

- Drop repeated claims (`_normalise` is provided), recording them in `duplicates`
- Compare the `window_hours` values that came back. Two or more, spread of 2 or more hours, means a conflict — name each department and its number
- Flag anything filed with `confidence < 0.5`

You can only check in code what you asked for as **data**. That is why `window_hours` is a number on the schema and not a sentence inside `claim`.

### 6. Implement `synthesise` and `lead_loop`

`synthesise` builds one line per finding, appends the conflicts `reconcile` found, and makes a single merge call with `MERGER_PROMPT`. Handing over the conflicts is the point: a model asked to merge "8 hours" and "3 hours" with no warning will quietly average them to five and a half.

`lead_loop` ties it together — lead turn with `tools=[SPAWN_TOOL]` and `parallel_tool_calls=True`, spawn whatever it asks for, stop when it stops spawning, then reconcile and merge. If it never spawned anything, just return its own answer.

### 7. Run the REPL

| Command | Action |
|---|---|
| any text | Research the question with the current mode |
| `/mode spawn` | The lead writes the briefs (default) |
| `/mode fixed` | Hand-written briefs, run concurrently |
| `/mode serial` | Hand-written briefs, one at a time — compare the timings |
| `/workers N` | Cap concurrent subagents (default 3) |
| `/trace` | Briefs, claims, and the merge step from the last question |
| `/archives` | List the departments |
| `quit` | Exit |

## Try it

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-09-multi-agent/exercises/05-subagents
python start.py

# Option B - uv (no activation needed):
cd module-09-multi-agent/exercises/05-subagents
uv run python start.py
```

Things worth trying:

- `Should the Pathfinder commit to the Vega Station rescue, and in what order?` then `/trace` — see which briefs the lead wrote for itself
- `/mode serial` then `/mode fixed` on the same question — the archive reads sleep 1s each, so the gap is visible
- `/workers 1` with `/mode fixed` — a cap of one is serial with extra steps
- Ask something narrow (`How many survivors are there?`) and watch the lead spawn one subagent instead of three

## Tests

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-09-multi-agent/exercises/05-subagents
pytest test_start.py -v

# Option B - uv (no activation needed):
cd module-09-multi-agent/exercises/05-subagents
uv run --extra dev pytest test_start.py -v
```

Tests use a mocked OpenAI client — no real API calls. One of them checks that four 50ms subagents finish in well under 200ms, so a `fan_out` that secretly awaits in a loop will fail it.

## Stretch goals

- **Depth cap.** Give subagents their own `spawn_researchers` tool and watch a child spawn grandchildren. Add a `depth` argument and refuse past depth 2.
- **Overlap detection.** Before spawning, compare the briefs the lead wrote and warn when two of them ask for the same thing — duplicated work costs twice and reads like corroboration.
- **Budget.** Count subagent calls per question and stop spawning when the budget is spent, returning what you have rather than failing.
- **Confidence weighting.** When the window numbers conflict, prefer the report with the higher confidence and the more recent archive record instead of asking the merger to adjudicate.
- **Dissent log.** Write every dropped duplicate and every conflicting claim to a JSONL file. The minority report is the thing you will want when the decision turns out wrong.
