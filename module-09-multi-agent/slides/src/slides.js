export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 9 — Multi-Agent Systems',
      subtitle: 'Roles, coordination, and shared context across cooperating agents',
      icon: 'users',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Decide **when** multi-agent designs are worth the complexity.',
        'Model **roles**: router, researcher, critic, supervisor, executor.',
        'Implement **coordination patterns**: supervisor, swarm, debate, consensus.',
        'Share **context and tools** safely across agents.',
        'Apply **consensus** and conflict resolution strategies.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'When to go multi-agent',
      icon: 'git-branch',
      points: [
        '**Yes**: different expertise needed (finance vs legal vs technical).',
        '**Yes**: critic/reviewer improves quality of high-stakes answers.',
        '**Yes**: parallel research on independent sub-questions.',
        '**No**: single-domain Q&A where one prompt + tools suffices.',
        '**No**: latency-sensitive paths where an extra round-trip hurts.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Common agent roles',
      icon: 'user',
      points: [
        '**Router**: classifies the query and dispatches to the right specialist.',
        '**Specialist**: domain expert with a focused system prompt and tools.',
        "**Critic**: reviews another agent's output for accuracy and gaps.",
        '**Supervisor**: orchestrates the team, merges results, decides when done.',
        '**Executor**: takes the final plan and runs it (deploy, notify, write).',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Router + specialist agents',
      code: `SPECIALISTS = {
    "finance": fin_agent,
    "technical": tech_agent,
    "legal": legal_agent,
}

def classify(query, client):
    """LLM returns JSON: {"department": "..."}"""
    ...

def route(query, client):
    dept = classify(query, client)
    return SPECIALISTS[dept].run(query, client)

# "What is our budget?" → finance
# "Why is the API slow?" → technical
# "Review the contract terms" → legal`,
      highlights: [
        'LLM-based classification with JSON mode — robust to ambiguous queries',
        'Each specialist has its own system prompt and domain focus',
      ],
    },
  },

  // ---- Demo break 1 ----
  {
    type: 'title',
    content: {
      title: 'Demo — Specialist agents + router',
      subtitle: 'Switch to terminal: python demo/demo.py — Part 1',
      icon: 'rocket',
    },
  },

  // ---- Section: Coordination ----
  {
    type: 'title',
    content: {
      title: 'Coordination patterns',
      subtitle: 'Supervisor, debate, and other ways to organise cooperating agents',
      icon: 'git-branch',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Coordination patterns',
      icon: 'git-branch',
      points: [
        '**Supervisor**: one lead agent delegates tasks and merges results.',
        '**Swarm**: agents self-organise, passing context peer-to-peer.',
        '**Debate**: two agents argue opposing views; a judge decides.',
        '**Blackboard**: shared state that agents read and write to.',
        '**Task queue**: agents pull work items from a shared queue.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Supervisor-critic pipeline',
      code: `def supervisor(query, client):
    dept = classify(query, client)
    answer = specialist(dept, query, client)

    for _ in range(max_revisions):
        review = critic.review(query, answer)
        if review["approved"]:
            return answer

        answer = specialist.revise(
            query, answer, review["feedback"]
        )

    return answer  # best effort after N rounds`,
      highlights: [
        'Supervisor controls flow: classify → respond → review → revise',
        'Critic feedback is fed back as context for improvement',
      ],
    },
  },

  // ---- Demo break 2 ----
  {
    type: 'title',
    content: {
      title: 'Demo — Supervisor-critic pipeline',
      subtitle: 'Switch to terminal: demo/demo.py — Part 2',
      icon: 'rocket',
    },
  },

  // ---- Section: Debate ----
  {
    type: 'title',
    content: {
      title: 'Debate pattern',
      subtitle: 'Adversarial agents stress-test decisions before commitment',
      icon: 'scale',
    },
  },
  {
    type: 'code',
    content: {
      title: 'Debate pattern',
      code: `def debate(question, client, rounds=2):
    for r in range(rounds):
        advocate_arg = advocate.argue(question)
        skeptic_arg = skeptic.counter(advocate_arg)

    return judge.decide(
        advocate_arg, skeptic_arg
    )

# Advocate: "Migrating saves 3 sprints..."
# Skeptic:  "Migration risk is too high..."
# Judge:    "The skeptic's risk case wins."`,
      highlights: [
        'Multiple rounds sharpen arguments before the judge decides',
        "Useful for high-stakes decisions where you want a devil's advocate",
      ],
    },
  },

  // ---- Demo break 3 ----
  {
    type: 'title',
    content: {
      title: 'Demo — Structured debate',
      subtitle: 'Switch to terminal: demo/demo.py — Part 3',
      icon: 'rocket',
    },
  },

  // ---- Section: Shared context & consensus ----
  {
    type: 'title',
    content: {
      title: 'Shared context + consensus',
      subtitle: 'How agents share data and resolve disagreements',
      icon: 'check-square',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Shared context and tools',
      icon: 'lock',
      points: [
        'Agents can share a **common tool registry** — same tools, same schemas.',
        'Or each agent gets a **scoped subset** of tools (principle of least privilege).',
        'Shared **context object**: conversation so far, retrieved documents, decisions.',
        'Watch for **race conditions** if agents run in parallel and write to shared state.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Consensus and conflict resolution',
      icon: 'check-square',
      points: [
        '**Voting**: N agents answer independently; majority wins.',
        '**Ranked choice**: agents score or rank proposals; aggregate.',
        '**Confidence weighting**: trust the agent that is most sure.',
        '**Tie-breaking**: supervisor or fallback rule decides deadlocks.',
        '**Log dissent**: record minority opinions for audit and debugging.',
      ],
    },
  },

  // ---- Demo break 4 ----
  {
    type: 'title',
    content: {
      title: 'Demo — Consensus voting',
      subtitle: 'Switch to terminal: demo/demo.py — Part 4',
      icon: 'rocket',
    },
  },

  // ---- Section: Swarm ----
  {
    type: 'title',
    content: {
      title: 'Swarm + handoffs',
      subtitle: 'Peer-to-peer agents with scoped tools — no central supervisor',
      icon: 'users',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Swarm vs supervisor',
      icon: 'git-branch',
      points: [
        '**Supervisor**: one agent decides who runs next (router, critic loop).',
        '**Swarm**: the active agent decides — use a tool, answer, or **hand off**.',
        'Each agent gets a **scoped tool set** (principle of least privilege).',
        '**Handoff** is a tool: `transfer_to_engineering` passes full context.',
        'More hops = more latency; cap with `max_hops` and log the chain.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Swarm loop with handoffs',
      code: `def swarm_loop(query, client, start="comms"):
    dept = start
    messages = build_messages(dept, query)
    chain = [dept]

    for hop in range(max_hops):
        msg = run_turn(dept, messages, tools=AGENT_TOOLS[dept])
        if not msg.tool_calls:
            return msg.content, chain

        tool_msgs, transfer = handle_tools(msg)
        messages.extend(tool_msgs)
        if transfer:
            dept = transfer
            chain.append(dept)
        # else: same agent, another tool round

# comms -> engineering -> final answer`,
      highlights: [
        'No supervisor — handoff is just another tool call',
        'Each department sees only its domain tools + transfer_to_*',
      ],
    },
  },

  // ---- Demo break 5 ----
  {
    type: 'title',
    content: {
      title: 'Demo — Swarm + tool handoffs',
      subtitle: 'Switch to terminal: demo/demo.py — Part 5',
      icon: 'rocket',
    },
  },

  // ---- Section: Wrap-up ----
  {
    type: 'title',
    content: {
      title: 'Putting it all together',
      subtitle: 'When to use multi-agent — and when not to',
      icon: 'lightbulb',
    },
  },
  {
    type: 'comparison',
    content: {
      title: 'Single agent vs multi-agent',
      left: {
        label: 'Single agent',
        items: [
          'Simpler to build and debug',
          'Lower latency (one LLM call path)',
          'All context in one conversation',
          'Sufficient for most use cases',
        ],
      },
      right: {
        label: 'Multi-agent',
        items: [
          'Specialist prompts = better per-domain quality',
          'Critic/reviewer catches errors',
          'Parallel execution for independent tasks',
          'Higher operational complexity',
        ],
      },
    },
  },
  {
    type: 'rules',
    content: {
      title: 'Field rules — Module 9',
      rules: [
        {
          rule: 'Justify every agent',
          example: 'If one prompt can do it, one agent should do it.',
          icon: 'scale',
        },
        {
          rule: 'Scope tools per agent',
          example: 'The critic should not delete production data.',
          icon: 'lock',
        },
        {
          rule: 'Log the full conversation trace',
          example: 'When multi-agent goes wrong, you need the whole picture.',
          icon: 'clipboard-list',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises',
      points: [
        '01 — Router agent: classify queries and dispatch to specialist agents',
        '02 — Supervisor-critic: orchestrate specialists with a quality review loop',
        '03 — Debate + consensus: argue, judge, and vote across multiple agents',
        '04 — Swarm tools: scoped tools and peer-to-peer handoffs between agents',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Module 9 — Complete',
      subtitle: 'Next: frameworks with LangChain',
      icon: 'check-circle',
    },
  },
];
