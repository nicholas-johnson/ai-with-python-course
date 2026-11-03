export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 8 — Structured Workflows',
      subtitle: 'Deciding how much of the control flow to hand to the model',
      icon: 'route',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'One question runs through this module',
      points: [
        'Every agent you have built so far lets the model decide what happens next.',
        'That is a choice, not a default — and usually the most expensive one available.',
        'Today: the spectrum from code-driven to model-driven, and where to sit on it.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Place a task on the **control-flow spectrum**: chain, router, plan-and-execute, ReAct.',
        'Build a **ReAct loop** whose reasoning is visible, with guards that stop it running away.',
        'Build **plan-and-execute**, and exploit the fact that a plan is data.',
        'Run independent plan steps **concurrently**, and **pause a plan** for human approval.',
      ],
    },
  },

  // ---- Section: the spectrum ----
  {
    type: 'title',
    content: {
      title: 'Who owns the control flow?',
      subtitle: 'Your code, or the model',
      icon: 'sliders',
    },
  },
  {
    type: 'description',
    content: {
      title: 'The only question that matters',
      description:
        'Not "ReAct or planning?" but **how many decisions am I handing to the model** — because every one of those is a decision I cannot unit test.',
      icon: 'help-circle',
    },
  },
  {
    type: 'cards',
    content: {
      title: 'The control-flow spectrum',
      cards: [
        {
          heading: '1. Fixed chain',
          points: [
            '**Code decides** every step',
            'The model only generates text',
            'Fully testable, cheapest, fastest',
            'Breaks on anything unanticipated',
          ],
        },
        {
          heading: '2. Router',
          points: [
            '**Model picks a branch**, code runs it',
            'One decision, and it is auditable',
            'Still cheap and still testable',
            'You must enumerate the branches',
          ],
        },
        {
          heading: '3. Plan-and-execute',
          points: [
            '**Model decides once**, up front',
            'Code executes the plan',
            'The plan is data: show it, store it, resume it',
            'A bad plan fails the whole run',
          ],
        },
        {
          heading: '4. ReAct',
          points: [
            '**Model decides every step**',
            'Adapts to whatever it finds',
            'Most expensive, slowest, hardest to test',
            'Can loop, wander, or never finish',
          ],
        },
      ],
    },
  },
  {
    type: 'three-way',
    content: {
      title: 'Same job, three places on the spectrum',
      left: {
        label: 'Fixed chain',
        code: `# you wrote
# the order
a = check("reactor")
b = check("shields")
c = search_logs(q)

summarise([a, b, c])

# model calls: 1
# decisions:   0`,
      },
      middle: {
        label: 'Plan-and-execute',
        code: `# model wrote
# the order, once
plan = make_plan(goal)

for step in plan:
    run(step)

summarise(results)

# model calls: 2+
# decisions:   1`,
      },
      right: {
        label: 'ReAct',
        code: `# model decides
# every turn
while not done:
    s = decide(msgs)
    if s.final:
        break
    obs = run(s)
    msgs += obs

# decisions:   N`,
      },
    },
  },
  {
    type: 'standard',
    content: {
      title: 'The rule: push left',
      icon: 'arrow-right',
      points: [
        'Start at the **left** and move right only when the task actually breaks.',
        'Moving right buys **adaptability**. It costs tokens, latency, and testability.',
        'Most production "agents" are a chain or a router wearing a trench coat — and that is fine.',
        'Reach for ReAct when you genuinely **cannot know the steps** until you see the data.',
        'The spectrum is per-task, not per-product. One app can use all four.',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Demo — one task, four strategies',
      subtitle: 'Switch to terminal: python demo/01_control_flow.py',
      icon: 'rocket',
    },
  },

  // ---- Section: ReAct ----
  {
    type: 'title',
    content: {
      title: 'ReAct',
      subtitle: 'Reason → Act → Observe, and the guards it needs',
      icon: 'refresh-cw',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'You already built most of this',
      icon: 'wrench',
      points: [
        'Module 2 gave you the loop: call the model, run the tool, feed the result back.',
        'ReAct adds one thing — the model must say **why** before it acts.',
        'That reasoning is what turns a tool log into a trace that explains itself.',
        'It is also a steering wheel: you can prompt against the reasoning, not just the actions.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'The trap: a Thought that is never there',
      icon: 'alert-triangle',
      points: [
        'The obvious move is to read the thought from `response.output_text`.',
        'But with native tool calling, that text is usually **empty** when the model emits a call.',
        'So you log a "Thought" field that is blank on every step that actually did something.',
        'Fix: make the thought a **required field on the schema**. Then it cannot go missing.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Make the reasoning structural',
      code: `class ReActStep(BaseModel):
    thought: str                      # required - cannot come back empty
    action: Literal["check_system", "search_logs",
                    "calculator", "final_answer"]
    action_input: str

response = client.responses.parse(
    model=MODEL, reasoning={"effort": "none"},
    text_format=ReActStep, input=messages,
)
step = response.output_parsed`,
      highlights: [
        'The schema, not the prompt, is what guarantees a thought on every turn',
        '`final_answer` is just another action — one clean exit from the loop',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'The loop, with its guards',
      code: `seen = set()
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

return force_an_answer(messages)        # guard 3: never return None`,
      highlights: [
        'Without guard 2 a stuck model spends the whole budget on one tool',
        'Without guard 3 a timeout returns nothing at all, which is worse than a partial answer',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Three guards, and why each exists',
      icon: 'shield',
      points: [
        '**Step budget** — bounds the worst case. Without it, cost is unbounded.',
        '**No-progress detection** — a repeated call returns an observation it has already seen.',
        '**Forced finalisation** — out of budget means answer with what you have, not return `None`.',
        'A cost ceiling is the fourth: stop on tokens spent, not just steps taken.',
        'Log the whole trace. When it goes wrong at 3am, the trace is the only evidence.',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Demo — ReAct and its guards',
      subtitle: 'Switch to terminal: python demo/02_react.py',
      icon: 'rocket',
    },
  },

  // ---- Section: plan-and-execute ----
  {
    type: 'title',
    content: {
      title: 'Plan-and-execute',
      subtitle: 'Decide once, then carry it out',
      icon: 'clipboard-list',
    },
  },
  {
    type: 'code',
    content: {
      title: 'Plan, execute, re-plan',
      code: `def plan_and_execute(goal, client, max_replans=1):
    plan = generate_plan(goal, client)      # one model decision
    completed = []

    for i, step in enumerate(plan):
        try:
            step.result = execute_step(step, client)
            step.status = "done"
        except Exception as e:
            step.status = "failed"
            if max_replans > 0:                 # re-plan what is left
                plan = completed + revise_plan(plan[i+1:], completed, e, client)
                max_replans -= 1
        completed.append(step)

    return synthesise(goal, completed, client)`,
      highlights: [
        'Cap `max_replans` — re-planning on every failure is an infinite loop with extra steps',
        'The executor for one step can itself be a small ReAct loop',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'The real payoff: the plan is data',
      icon: 'file-text',
      points: [
        'A ReAct loop lives in a call stack. A plan is a **list of objects**.',
        'You can **show it to a user** before anything runs — the single best UX win here.',
        'You can **store it**, diff intended against actual, and replay it in tests.',
        'You can **schedule it** — which is the next slide.',
        'You can **stop in the middle of it** — which is the slide after that.',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Demo — plan-and-execute',
      subtitle: 'Switch to terminal: python demo/03_plan_and_execute.py',
      icon: 'rocket',
    },
  },

  // ---- Section: the plan is a graph ----
  {
    type: 'title',
    content: {
      title: 'A plan is a graph, not a list',
      subtitle: 'The thing ReAct structurally cannot do',
      icon: 'git-branch',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Why ReAct is always serial',
      icon: 'clock',
      points: [
        'ReAct picks its next action **after reading the last observation**.',
        'So every step waits on the one before it — even when the work is independent.',
        'Checking four ship systems has no ordering constraint, but ReAct checks them one at a time.',
        'A plan written up front can **declare** what depends on what.',
        'One extra field on the schema turns the list into a schedule.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'depends_on, and the waves it implies',
      code: `class PlannedStep(BaseModel):
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
    return levels`,
      highlights: [
        'Tell the planner not to invent dependencies — a false one costs you the speed-up',
        'Always handle the cycle case: a confused plan should still run, not deadlock',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Run each wave concurrently',
      code: `async def run_parallel(levels, client):
    results = {}
    for wave in levels:
        completed = await asyncio.gather(
            *(execute_step(step, results, client) for step in wave)
        )
        for step, result in zip(wave, completed, strict=True):
            results[step.number] = result
    return results

# inside execute_step, keep blocking tools off the event loop:
result = await asyncio.to_thread(run_tool, call.name, call.arguments)`,
      highlights: [
        'Six steps in two waves finish in the time of two steps, not six',
        'A blocking tool called directly would serialise the whole wave',
      ],
    },
  },
  {
    type: 'comparison',
    content: {
      title: 'ReAct vs plan-and-execute, concretely',
      left: {
        label: 'ReAct',
        items: [
          'Serial by construction',
          'Nothing to show until it finishes',
          'Dies with the process',
          'Cannot pause for a human',
          'Adapts the instant something surprises it',
        ],
      },
      right: {
        label: 'Plan-and-execute',
        items: [
          'Independent steps run concurrently',
          'Show the plan before running it',
          'Checkpoint to disk, resume later',
          'Block on approval mid-plan',
          'Only adapts when a step fails',
        ],
      },
    },
  },
  {
    type: 'title',
    content: {
      title: 'Demo — parallel plans',
      subtitle: 'Switch to terminal: python demo/04_parallel_plan.py',
      icon: 'rocket',
    },
  },

  // ---- Section: approval and resume ----
  {
    type: 'title',
    content: {
      title: 'Pause, approve, resume',
      subtitle: 'What you get for free once the plan is on disk',
      icon: 'shield',
    },
  },
  {
    type: 'code',
    content: {
      title: 'The approval gate',
      code: `NEEDS_APPROVAL = {"file_report", "book_flight", "send_email"}

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
    return "complete"`,
      highlights: [
        'Skipping completed steps is what makes resuming safe to call repeatedly',
        'Save after every step — a crash should cost you one step, not the run',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Code decides what is dangerous',
      icon: 'lock',
      points: [
        'Let the **code** flag which tools need approval, from a fixed allowlist.',
        'A plan that marks **its own** steps as safe is not a safety control.',
        'Gate on the irreversible: money, messages, writes to a permanent record.',
        'Checkpoint after every step, so a crash costs one step rather than the whole run.',
        'Resuming must be **idempotent** — the guard is the status field, and you must test it.',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Demo — approval and resume',
      subtitle: 'Switch to terminal: python demo/05_approval_resume.py',
      icon: 'rocket',
    },
  },

  // ---- Wrap-up ----
  {
    type: 'title',
    content: {
      title: 'Putting it all together',
      subtitle: 'Summary and exercises',
      icon: 'check-square',
    },
  },
  {
    type: 'rules',
    content: {
      title: 'Summary',
      rules: [
        {
          rule: 'Push control flow as far left as the task allows',
          example:
            'Chain, then router, then plan, then ReAct. Move right only when the task breaks.',
          icon: 'sliders',
        },
        {
          rule: 'Make the reasoning structural, not hopeful',
          example:
            'A required `thought` field always arrives. One read off `output_text` usually does not.',
          icon: 'brain',
        },
        {
          rule: 'Every loop needs a budget, a repeat check, and a forced exit',
          example:
            'Unbounded cost, a model going in circles, and returning None are all production outages.',
          icon: 'shield',
        },
        {
          rule: 'The plan is data — that is the whole point',
          example:
            'Show it, schedule it in waves, checkpoint it, and pause it for a human.',
          icon: 'file-text',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises — workflows in action',
      points: [
        '01 — ReAct agent: a visible thought, plus a step budget and a repeat guard',
        '02 — Plan-and-execute: planner and executor, with re-planning on failure',
        '03 — Parallel and approval: depends_on waves, checkpointing, and a human gate',
        '04 — Holiday Planner app: the full web app with plan visualisation',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Module 8 — Complete',
      subtitle: 'Next: multi-agent systems',
      icon: 'check-circle',
    },
  },
];
