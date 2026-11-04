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
        '**Spawn subagents** in parallel and reconcile what they send back.',
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
        '**Yes**: Context window management is needed.',
        '**Yes**: reduce costs by giving simple tasks to smaller agents.',
        '**No**: single-domain Q&A where one prompt + tools suffices.',
        '**No**: latency-sensitive paths where an extra round-trip hurts.',
      ],
      credit:
        'Xi et al. (2023). "The Rise and Potential of Large Language Model Based Agents: A Survey." arXiv:2309.07864',
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
        '**Planner**: writes the plan based on the query and the context.',
        '**Conflict Resolver**: fixes conflicting results from the agents.',
        '**Reporter**: reports the final answer to the human user.',
      ],
      credit:
        'Li et al. (2023). "CAMEL: Communicative Agents for “Mind” Exploration of Large Language Model Society." arXiv:2303.17760',
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
        'LLM-based classification with structured outputs — a Literal schema means only valid departments come back',
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
        '**Spawn**: the lead creates subagents on demand and merges their reports.',
        '**Blackboard**: shared state that agents read and write to.',
        '**Task queue**: agents pull work items from a shared queue.',
      ],
      credit:
        'Wu et al. (2023). "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation." arXiv:2308.08155',
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
      credit:
        'Shinn et al. (2023). "Reflexion: Language Agents with Verbal Reinforcement Learning." arXiv:2303.11366',
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
      credit:
        'Du et al. (2023). "Improving Factuality and Reasoning in Language Models through Multiagent Debate." arXiv:2305.14325',
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
      credit:
        'Wang et al. (2022). "Self-Consistency Improves Chain of Thought Reasoning in Language Models." arXiv:2203.11171',
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
      ],
      credit:
        'Park et al. (2023). "Generative Agents: Interactive Simulacra of Human Behavior." arXiv:2304.03442',
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
        if not calls:
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

  // ---- Section: Spawning subagents ----
  {
    type: 'title',
    content: {
      title: 'Spawning subagents',
      subtitle: 'Agents created on demand, run in parallel, reports merged back',
      icon: 'share-2',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Route, hand off, or spawn',
      icon: 'git-branch',
      points: [
        '**Route**: pick one agent from a roster you wrote. Control returns to you.',
        '**Hand off**: the active agent passes control sideways and does not get it back.',
        '**Spawn**: the lead creates a worker on demand, gets a result, keeps control.',
        'A subagent is a **context window**, not a job title — same model, new conversation.',
        'Spawn when work is **independent**; hand off when the *domain* changed.',
      ],
      credit:
        'Zhou et al. (2022). "Least-to-Most Prompting Enables Complex Reasoning in Large Language Models." arXiv:2205.10625',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Context Mamagement and Speed',
      icon: 'layers',
      points: [
        'A subagent reads 30 tool results; the lead only ever sees its **summary**.',
        'The lead stays small, so it stays coherent over a long task.',
        'Parallelism is useful — three 8s researchers finish in 8s, not 24s.',
        'The cost: the child cannot see the parent conversation, so the brief must stand alone.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Fan-out with a cap',
      code: `async def fan_out(briefs, client, max_workers=3):
    limit = asyncio.Semaphore(max_workers)

    async def guarded(brief):
        async with limit:
            return await run_subagent(brief, client)

    settled = await asyncio.gather(
        *(guarded(b) for b in briefs),
        return_exceptions=True,      # one failure must
    )                                # not cancel the rest

    return [
        finding if not isinstance(finding, BaseException)
        else stub(brief, finding)    # keep the slots aligned
        for brief, finding in zip(briefs, settled)
    ]`,
      highlights: [
        'Module 8 parallelised plan steps with depends_on — same gather, agents instead of steps',
        'Semaphore caps concurrency; return_exceptions keeps a crashed worker from taking the batch',
        'Return results aligned with the briefs, so finding i still matches tool call i',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'The subagent is a tool',
      code: `SPAWN_TOOL = {
    "type": "function",
    "name": "spawn_researchers",
    "description": (
        "Research independent sub-questions, each "
        "in its own context. Pass every brief in "
        "one call - they all run at once. Max 3."
    ),
    "parameters": {...},   # briefs: [{department, task}]
}

briefs = to_briefs(spawn_calls(response))  # it wrote
findings = await fan_out(briefs, client)   # you ran

# The output carries the reports only - never
# the children's transcripts.`,
      highlights: [
        'The model chooses how many to spawn and what to ask',
        'It will validate the agent choice against a dictionary of allowed agents',
        'This is the Task tool in Cursor and Claude Code',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Reconciling what comes back',
      icon: 'check-square',
      points: [
        '**Always preserve Provenance**: the parent must know where each claim came from.',
        '**Deterministic merge**: dedupe claims, keep provenance.',
        '**LLM synthesis**: one merge call — and tell it what the code already flagged.',
        '**Structured responses** are easier to merge than prose.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'How it goes wrong',
      icon: 'alert-triangle',
      points: [
        '**Overlapping briefs**: two children do the same work and look like corroboration.',
        '**Unbounded spawning**: children spawning children. Cap depth and total calls.',
        '**Cost multiplies**, latency does not.',
        '**Lost provenance**: the parent attaches the source, never the child.',
        '**Silent drops**: Workers may fail. LLMs are non-deterministic.',
      ],
      credit:
        'Cemri et al. (2025). "Why Do Multi-Agent LLM Systems Fail?" arXiv:2503.13657',
    },
  },

  // ---- Demo break 6 ----
  {
    type: 'title',
    content: {
      title: 'Demo — Spawned subagents',
      subtitle: 'Switch to terminal: demo/demo.py — Part 6',
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
          'Subagent contexts stay out of the lead',
          'Higher operational complexity',
        ],
      },
    },
  },
  {
    type: 'rules',
    content: {
      title: 'Summary',
      rules: [
        {
          rule: 'One agent until you can justify another',
          example: 'If one prompt can do it, one agent should do it.',
          icon: 'scale',
        },
        {
          rule: 'Roles stay narrow',
          example:
            'Router, specialist, critic, supervisor. Overlap means duplicate work.',
          icon: 'users',
        },
        {
          rule: 'Pick one coordination pattern',
          example: 'Supervisor, swarm, debate, or consensus — and stick to it.',
          icon: 'git-branch',
        },
        {
          rule: 'Scope tools and log the trace',
          example:
            'The critic should not delete production data. Keep the whole conversation.',
          icon: 'lock',
        },
        {
          rule: 'A subagent is a context window',
          example:
            'Spawn for isolation, cap the workers, and never average a conflict away.',
          icon: 'share-2',
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
        '05 — Subagents: spawn researchers in parallel, then reconcile their reports',
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
