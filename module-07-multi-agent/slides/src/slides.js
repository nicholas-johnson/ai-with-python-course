export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 7 — Multi-Agent Systems',
      subtitle: 'Roles, coordination, and shared context aboard the Pathfinder',
      icon: 'users',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Many minds, one mission',
      points: [
        'Sometimes one agent is not enough — and sometimes it is.',
        'Multi-agent adds latency and failure modes. Use it when it earns its keep.',
        'Roles, coordination patterns, shared tools, and conflict resolution.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Decide **when** multi-agent designs are worth the complexity.',
        'Model **roles**: router, researcher, coder, critic, executor.',
        'Implement **coordination patterns**: supervisor, swarm, debate.',
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
        '**Yes**: different expertise needed (navigation vs science vs engineering).',
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
      icon: 'briefcase',
      points: [
        '**Router**: classifies the query and dispatches to the right specialist.',
        '**Researcher**: retrieves data, searches logs, calls tools.',
        '**Critic**: reviews another agent\'s output for accuracy and gaps.',
        '**Supervisor**: orchestrates the team, merges results, decides when done.',
        '**Executor**: takes the final plan and runs it (deploy, notify, write).',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Router agent',
      code: `SPECIALISTS = {
    "navigation": nav_agent,
    "engineering": eng_agent,
    "science": sci_agent,
}

def route(query: str) -> str:
    department = classify(query)  # LLM or heuristic
    specialist = SPECIALISTS[department]
    return specialist.run(query)

# "What is our heading?" → navigation
# "Hull integrity report" → engineering
# "Analyse the nebula scan" → science`,
      highlights: [
        'Classification can be LLM-based or simple keyword rules',
        'Each specialist has its own system prompt and tools',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Coordination patterns',
      icon: 'network',
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
      title: 'Supervisor pattern',
      code: `def supervisor(query):
    research = researcher.run(query)
    critique = critic.run(
        f"Review this research for accuracy:\\n{research}"
    )

    if "APPROVED" in critique:
        return research

    revised = researcher.run(
        f"Original: {research}\\nFeedback: {critique}\\n"
        f"Revise your answer."
    )
    return revised`,
      highlights: [
        'Supervisor controls flow: research → review → revise',
        'Critic feedback is fed back as context for improvement',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Debate pattern',
      code: `def debate(question, rounds=2):
    pro_arg = pro_agent.run(f"Argue FOR: {question}")
    con_arg = con_agent.run(f"Argue AGAINST: {question}")

    for _ in range(rounds):
        pro_arg = pro_agent.run(
            f"Counter this: {con_arg}"
        )
        con_arg = con_agent.run(
            f"Counter this: {pro_arg}"
        )

    return judge_agent.run(
        f"PRO: {pro_arg}\\nCON: {con_arg}\\nDecide."
    )`,
      highlights: [
        'Multiple rounds sharpen arguments before the judge decides',
        'Useful for high-stakes planning where you want devil\'s advocate',
      ],
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
        '**Voting**: N agents answer; majority wins.',
        '**Ranked choice**: agents score or rank proposals; aggregate.',
        '**Confidence weighting**: trust the agent that is most sure.',
        '**Tie-breaking**: supervisor or fallback rule decides deadlocks.',
        '**Log dissent**: record minority opinions for audit and debugging.',
      ],
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
      title: 'Field rules — Module 7',
      rules: [
        {
          rule: 'Justify every agent',
          example: 'If one prompt can do it, one agent should do it.',
          icon: 'scale',
        },
        {
          rule: 'Scope tools per agent',
          example: 'The critic should not fire the weapons system.',
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
      title: 'Exercises — Assembling the crew',
      points: [
        '01 — Router agent: dispatch queries to navigation, engineering, science',
        '02 — Research team: supervisor + researcher + critic',
        '03 — Consensus: multiple proposals, vote, and resolve ties',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Crew assembled — Module 7',
      subtitle: 'The agents work together. Next: teach them to remember.',
      icon: 'party-popper',
    },
  },
];
