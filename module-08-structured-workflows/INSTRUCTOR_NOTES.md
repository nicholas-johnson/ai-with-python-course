# Module 8 — Instructor Notes

Delivery notes for Structured Workflows, the Day 2 closer. The course-wide [`instructor.md`](../instructor.md) has the one-page summary; this file is the detail: what the module covers, what to say, and what each demo is actually demonstrating.

---

## What this module covers

Five ideas, in order:

1. **The control-flow spectrum** — fixed chain, router, plan-and-execute, ReAct. The organising idea for the whole module.
2. **ReAct done properly** — a reasoning trace that is actually populated, and three guards that stop the loop running away.
3. **Plan-and-execute** — decide once up front, re-plan on failure.
4. **Parallel plans** — `depends_on` turns the plan into a graph you can schedule.
5. **Approval gates and checkpointing** — a plan on disk can pause for a human and survive a restart.

### What it deliberately does not cover

- **Multi-agent anything.** Supervisor, critic, debate and handoffs are Module 9. If someone asks "could a second agent review the plan?", the answer is "yes, and that's tomorrow morning."
- **Self-critique / reflection loops.** Same reason — Module 9 owns the critic. The single-agent version of that lesson lives here as loop control (stopping conditions), not as a critic.
- **Frameworks.** This module builds by hand what LangGraph gives you as typed state and a graph. Module 10 makes that connection explicitly; it lands much harder if you flag it here. One line is enough: "you are building LangGraph's state machine by hand, and on Day 3 you'll see the version with the batteries included."

### The honest framing of ReAct

Worth knowing before you teach it: **ReAct is not new to the delegates.** They built a tool-calling loop in Module 2. If you present ReAct as a brand-new pattern, sharp delegates will notice it is the same loop and quietly disengage.

Present it instead as *Module 2's loop plus one addition — the model has to say why.* That is honest, and it sets up the genuinely new material (the guards).

---

## The spine: who owns the control flow

If delegates leave with one thing, it is this:

> The question is not "ReAct or planning?" It is **how many decisions am I handing to the model** — because each one is a decision I cannot unit test. Push control flow as far left as the task allows.

Things worth saying out loud:

- **"Most production agents are a chain or a router wearing a trench coat."** Gets a laugh, and it gives people permission to not build a ReAct agent. A lot of delegates arrive assuming "agent" means "fully autonomous loop" and that is usually the wrong default.
- **The spectrum is per-task, not per-product.** One application can and should use all four. The routing endpoint is a router; the research endpoint is ReAct.
- **Moving right buys adaptability and costs tokens, latency, and testability.** All three, every time. There is no free move.

Expect pushback along the lines of "but the model is smart enough now." The counter is not about capability, it is about **testability and blast radius**: you can write a unit test for a branch, you cannot write one for a decision the model makes differently each time.

---

## Talk track, section by section

### 1. The spectrum (slides 4–9)

Open on the cards slide — four columns, who decides, cost, testability. Then the three-way code slide, which shows the same job written as a chain, a plan, and a ReAct loop side by side. Point at the comment lines: `# decisions: 0` versus `# decisions: N`. That is the entire module in one slide.

Land the push-left rule before the demo, so the demo confirms something they already believe rather than introducing it cold.

### 2. ReAct (slides 10–16)

Beats in order:

- **"You already built this in Module 2."** Say it first, explicitly.
- **The trap.** The obvious implementation reads the thought from `response.output_text`. With native tool calling that text is *empty* whenever the model emits a call — so you log a Thought field that is blank on exactly the steps that did something. This is a real bug people ship; it is worth dwelling on.
- **The fix is structural, not prompt engineering.** A required `thought` field on the response schema cannot come back missing. Contrast with "please explain your reasoning" in a system prompt, which is a request, not a guarantee.
- **Three guards**, and why each exists:
  - *Step budget* — bounds the worst case. Without it, cost is unbounded.
  - *No-progress detection* — a repeat returns an observation already in the context.
  - *Forced finalisation* — out of budget should produce a partial answer, never `None`.
- **The subtlety on guard 2**, which is the best discussion point in the module: a repeat is only pointless *if nothing changed*. `read_notes()` after a new `take_note()` is a perfectly sensible repeat. Hence `MUTATING_TOOLS` resetting the seen-set. Ask the room when strict repeat-blocking would be wrong before you show the answer.

### 3. Plan-and-execute (slides 17–20)

Keep this section brisk — conceptually it is the easiest part, and the interesting consequences are in the two sections after it.

The one line that matters: **the plan is data.** A ReAct loop lives in a Python call stack; a plan is a list of objects. Everything in sections 4 and 5 follows from that single property. Flag that you are about to cash it in twice.

Mention capping `max_replans` — re-planning on every failure is an infinite loop with extra steps.

### 4. Parallel plans (slides 21–26)

The strongest argument in the module, because it is a capability gap rather than a preference:

> ReAct picks its next action *after* reading the last observation. It is serial by construction — even when the work has no ordering constraint at all. Checking four ship systems has no ordering constraint, but ReAct checks them one at a time.

Two engineering points not to skip:

- **Tell the planner not to invent dependencies.** Models love to impose a sequential order that is not required, and every false dependency costs you a wave. This is prompt work with a measurable payoff.
- **Always handle the cycle case.** A confused plan should still run; it must never deadlock. The `if not ready:` branch is the whole fix.

### 5. Approval and resume (slides 27–30)

The key claim: **code decides what is dangerous, not the model.** A plan that can mark its own steps as safe is not a safety control — the model is the thing you are guarding against. Keep the irreversible-tool list in code where it can be reviewed and tested.

Then: checkpoint after every step so a crash costs one step rather than the run, and make resuming idempotent. Skipping completed steps is what stops a resume from booking the flight twice.

---

## The demos

Run via the menu: `python module-08-structured-workflows/demo/demo.py`. Each part also runs standalone, e.g. `python module-08-structured-workflows/demo/04_parallel_plan.py`.

Tools are shared in `demo/workflow_tools.py` so demo 01 compares the four strategies like for like. They sleep (default 0.8s) to stand in for real network calls — **set `DEMO_TOOL_LATENCY=0` for a fast dry run**, but leave the delay in during delivery or demo 04's speed-up vanishes.

All demos use the Deep Space Ops ship domain (reactor, shields, logs, missions). Note the domain shifts in the exercises — see the exercise section below.

### 01 — Who owns the control flow

Runs one task ("is MSN-001 safe to continue?") four ways: fixed chain, router, plan-and-execute, ReAct. Same tools throughout.

As each strategy runs it prints every step tagged `[code ]` or `[MODEL]`. Then a summary table:

```
  Strategy               LLM  Tools   Tokens  Seconds  Model decisions
  --------------------------------------------------------------------
  Fixed chain              1      3      ...      ...                 0
  Router                   2      ...    ...      ...                 1
  Plan-and-execute         ...    ...    ...      ...                 1
  ReAct                    ...    ...    ...      ...                 N
```

**What to point at:** the last column. Going down the table you hand the model more of the control flow; tokens and seconds go up with it. The numbers vary run to run — that variance is itself the point, and worth naming: the bottom row is the one you cannot predict.

**Caveat:** this is the longest demo because it runs four strategies with real latency. If you are short on time, this is the one to run once at the start and refer back to.

### 02 — ReAct, with the thought made visible

Two halves.

**First half** runs a real ReAct loop where `thought` is a required field on a `ReActStep` schema, so every step prints `Thought | ...` before its action. This is the contrast with Module 2 — show it, then say "in Module 2 that line would have been blank."

**Second half needs no API key.** It runs the same loop against `_StuckClient`, a stand-in that always asks for `check_system(shields)`. You get:

```
    Thought | I should check the shields.
    Action  | check_system(shields)
    Observe | Shields: 85% charge...
    Thought | I should check the shields.
    GUARD   | repeat of check_system, nudging
    GUARD   | repeat of check_system, nudging
    GUARD   | step budget of 4 exhausted, forcing an answer
    Answer  | Shields are at 85% and recharging...
```

**What to point at:** both guards firing, and the fact that it still returns an answer. Say the counterfactual explicitly — without guard 2 this burns the whole budget on one tool; without guard 3 it returns `None`. This half is reliable and fast, so it is the safest demo to run if the network is flaky.

### 03 — Plan-and-execute

Generates a plan, executes each step, synthesises. Prints the plan before running it.

**What to point at:** the plan appearing *before* any work happens. That is the UX win — you can show a user what is about to happen and let them stop it. Flag that the next two demos are both consequences of the plan being data.

### 04 — The plan is a graph

Generates a plan where each step carries `depends_on`, groups steps into waves, then runs the *same plan* twice — serially, then wave by wave — and reports both times:

```
  Scheduled into 2 waves:
    Wave 1: steps 1, 2, 3, 4  (4 concurrent)
    Wave 2: steps 5
  Running the plan serially...   12.4s
  Running the same plan wave by wave...   4.1s
  3.0x faster, from 5 steps in 2 waves
```

**What to point at:** the wave breakdown and the speed-up. Then the punchline — ReAct cannot do this, no matter how good the model gets, because it does not know step 3 exists until step 2 comes back.

**If the speed-up is small**, the planner invented dependencies and serialised its own plan. Do not hide this — it is the most useful failure in the module. Show the `depends_on` list, point out the unnecessary edge, and connect it to the prompt instruction telling the planner not to invent ordering. Re-running usually gives a better plan.

### 05 — Pause, approve, resume

Plans an investigation ending in `file_report` (irreversible). Runs until it hits that step, marks it `awaiting_approval`, writes the checkpoint, and stops. Then reloads from disk, approves, and resumes — printing `already done, skipping` for the completed steps.

**What to point at:**

- The gated step did **not** run. The side effect has not happened.
- The state is on disk — `.workflow_state.json`, worth opening in the editor mid-demo. The process could exit here and lose nothing.
- On resume, finished steps are skipped. Say why that matters: this is the difference between resuming and booking the flight twice.
- `requires_approval` was set by **code** from the tool name, not proposed by the model.

**Occasional flake:** if the planner does not schedule a gated step, the demo says so and exits early. Just re-run.

---

## Exercises

Four, chained. Delegates can carry their own code forward or use the provided solution.

| Folder | What they build | Where they get stuck |
| ------ | --------------- | -------------------- |
| `01-react-agent` | ReAct loop with the three guards | The repeat guard: most write it as a blanket block and are surprised by the `MUTATING_TOOLS` test. That surprise is intentional. |
| `02-plan-and-execute` | Planner + executor with re-planning | Threading context between steps; forgetting to cap `max_replans`. |
| `03-parallel-approval` | `depends_on` waves, approval gate, checkpoint | Writing `for step in wave: await ...` instead of `asyncio.gather`. There is a timing test that fails a serial implementation, so they find out. Also: forgetting to skip completed steps, which the resume test catches. |
| `04-holiday-planner` | FastAPI + Svelte app, SSE streaming | Backend only — the frontend is provided and expects a specific SSE event shape, documented in that exercise's README. |

**Note the domain shift.** The demos use the ship domain. Exercises 01 and 02 use a generic research assistant (web search, calculator, notes). Exercise 03 uses travel, which previews exercise 04's holiday planner. Call this out so nobody thinks they have lost the thread.

**Running tests:** per exercise, e.g. `pytest module-08-structured-workflows/exercises/01-react-agent/ -v`. A bare `pytest module-08-structured-workflows/` **cannot collect** — every exercise has a `test_start.py` and there are no package markers. This is true of every module in the course, not something specific to module 8; if a delegate hits it, that is the explanation.

Tests fail by design against the unimplemented `start.py`. That is the starting state, not a broken checkout.

---

## Questions you should expect

**"Isn't this just the Module 2 agent loop again?"**
For ReAct, essentially yes — say so. The new material is the visible reasoning and the guards. Getting ahead of this question is better than answering it defensively.

**"Why not always use ReAct, since models keep getting better?"**
Capability is not the constraint; testability and blast radius are. Also the structural one: no model improvement makes ReAct parallel, because it cannot know step 3 exists until step 2 returns.

**"Why not let the model decide which steps need approval?"**
Because the model is the thing you are guarding against. A plan that self-certifies as safe is not a safety control.

**"Isn't this what LangGraph does?"**
Yes — you are building its typed state and graph by hand. Module 10 shows the framework version. Building it once by hand is what makes the framework legible rather than magic.

**"What if a step fails halfway through a parallel wave?"**
Honest answer: the demo code doesn't handle partial wave failure — `asyncio.gather` propagates the first exception, so one bad step loses the results of its siblings. Production needs `return_exceptions=True` plus a per-step retry or re-plan. Good stretch discussion, and it connects to exercise 03's stretch goal about re-planning only the failed step's subtree.

---

## Setup and prerequisites

- `OPENAI_API_KEY` for everything except the second half of demo 02, which runs offline.
- Module 0's asyncio material is the prerequisite for demos 04 and 05 and exercise 03. If the group skipped Module 0, budget a couple of minutes on `asyncio.gather` before demo 04.
- Slides: `pnpm slides:08` from the repo root.
- `DEMO_TOOL_LATENCY=0` speeds up a dry run; leave it unset when presenting.
