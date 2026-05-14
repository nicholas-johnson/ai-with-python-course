export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 8 — Structured Workflows',
      subtitle: 'ReAct, plan-and-execute, and building agents that think before they act',
      icon: 'route',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'From reactive to deliberate',
      points: [
        'So far our agents respond to each message independently — no planning, no reasoning trace.',
        'Structured workflows add explicit reasoning steps between input and action.',
        'Two patterns dominate: ReAct (step-by-step) and plan-and-execute (full plan first).',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Build a **ReAct loop**: Thought → Action → Observation, with explicit traces.',
        'Build a **plan-and-execute** workflow: generate a plan, execute steps, re-plan on failure.',
        'Compare both patterns: when to use which, trade-offs in cost, latency, and reliability.',
        'Integrate workflows into a **web application** with streaming and plan visualisation.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'ReAct: Reason → Act → Observe',
      icon: 'refresh-cw',
      points: [
        '**Thought**: the agent reasons about what to do next (visible in logs).',
        '**Action**: it calls a tool with specific arguments.',
        '**Observation**: the tool result is fed back as context.',
        '**Loop**: repeat until the agent has enough to answer.',
        'Explicit reasoning traces make debugging much easier.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'ReAct loop',
      code: `def run_react(query, tools, client, max_steps=5):
    messages = [SYSTEM_PROMPT, {"role": "user", "content": query}]
    trace = []

    for step in range(max_steps):
        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages,
            tools=tool_schemas, tool_choice="auto",
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            trace.append({"type": "answer", "content": msg.content})
            return {"answer": msg.content, "trace": trace}

        for tc in msg.tool_calls:
            result = tools[tc.function.name](**json.loads(tc.function.arguments))
            trace.append({"type": "tool", "name": tc.function.name, "result": result})
            messages.append({"role": "tool", "content": result, "tool_call_id": tc.id})

    return {"answer": None, "trace": trace}`,
      highlights: [
        'Each step adds to the context — the LLM sees its own reasoning',
        'The trace records every tool call for debugging',
      ],
    },
  },
  {
    type: 'comparison',
    content: {
      title: 'ReAct vs plan-and-execute',
      left: {
        label: 'ReAct',
        items: [
          'Decide one step at a time',
          'Adapts to unexpected results',
          'Simple to implement',
          'Can wander if not constrained',
        ],
      },
      right: {
        label: 'Plan-and-execute',
        items: [
          'Make a full plan upfront',
          'Execute steps in order',
          'Better for known procedures',
          'Re-plan if a step fails',
        ],
      },
    },
  },
  {
    type: 'code',
    content: {
      title: 'Plan-and-execute',
      code: `async def plan_and_execute(goal, tools, client, max_replans=2):
    plan = generate_plan(goal, client)
    results = []

    for i, step in enumerate(plan):
        try:
            result = await execute_step(step, tools, client)
            results.append({"step": step, "result": result, "status": "done"})
        except Exception as e:
            results.append({"step": step, "error": str(e), "status": "failed"})
            if max_replans > 0:
                plan = revise_plan(plan[i+1:], results, client)
                max_replans -= 1

    return synthesise_answer(goal, results, client)`,
      highlights: [
        'The planner generates all steps up front',
        'If a step fails, remaining steps are revised',
      ],
    },
  },
  {
    type: 'rules',
    content: {
      title: 'Field rules — Module 8',
      rules: [
        {
          rule: 'Cap your loops',
          example: 'ReAct max_steps=10, plan-and-execute max_replans=2. Runaway agents waste tokens.',
          icon: 'shield',
        },
        {
          rule: 'Log the trace',
          example: 'Every Thought/Action/Observation or plan step — your best debugging tool.',
          icon: 'search',
        },
        {
          rule: 'Choose the right pattern',
          example: 'ReAct for exploration, plan-and-execute for structured multi-step tasks.',
          icon: 'git-branch',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises — Workflows in action',
      points: [
        '01 — ReAct agent: build a Thought → Action → Observation loop with real tools',
        '02 — Plan-and-execute: planner + executor with re-planning on failure',
        '03 — Holiday Planner app: full web app with plan visualisation',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Workflows online — Module 8',
      subtitle: 'Agents that plan before they act. Next: multi-agent coordination.',
      icon: 'party-popper',
    },
  },
];
