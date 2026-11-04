# Module 9 — Multi-Agent Systems

> One agent is useful. A crew of agents — each with a speciality, coordinated by a supervisor or handing off peer-to-peer — can tackle problems no single model could handle alone. The Pathfinder's bridge crew is the model: a commander routes queries, a science officer researches, an engineer inspects systems, and a critic reviews the work before it reaches the crew. In this module you design multi-agent architectures, build coordination patterns (supervisor, swarm, debate, consensus), and learn when multiple agents are worth the complexity.

## Learning goals

- Know **when to use** multi-agent systems (and when a single agent is better).
- Define **agent roles**: router, researcher, critic, supervisor, executor.
- Implement **coordination patterns**: supervisor, swarm, debate, blackboard, task queue.
- Share **context and tools** between agents safely.
- Build **conflict resolution** and consensus mechanisms.
- **Spawn subagents** on demand, run them in parallel, and reconcile their reports.

---

## When to use multi-agent systems

Multi-agent adds complexity — more messages, more coordination logic, higher token costs. Use it when:

- The task requires **distinct expertise** (navigation vs. engineering vs. science).
- You need **checks and balances** — a critic that reviews before publishing.
- The workload can be **parallelised** — multiple researchers searching different sources simultaneously.
- You want **separation of concerns** — each agent has a focused system prompt and tool set.

Do NOT use multi-agent when a single agent with good tools can handle the job. A crew member asking "What is the hull temperature?" does not need a supervisor, researcher, and critic — one tool call suffices.

---

## Agent roles

Each agent in a multi-agent system has a defined role with its own system prompt, tool access, and output format.

**Router** — the front door. Analyses the user's message and decides which specialist should handle it. Does not answer questions itself.

```python
def route(message: str) -> str:
    """Return the specialist name that should handle this message."""
    if any(kw in message.lower() for kw in ["navigate", "course", "heading"]):
        return "navigation"
    elif any(kw in message.lower() for kw in ["engine", "power", "reactor"]):
        return "engineering"
    else:
        return "science"
```

**Researcher** — gathers information using tools (RAG search, database queries, sensor reads). Returns structured findings, not polished prose.

**Critic** — reviews the researcher's output for accuracy, completeness, and hallucination. Can request a revision or approve.

**Supervisor** — orchestrates the workflow. Sends tasks to agents, collects results, decides when the answer is ready. This is the pattern you will implement most often.

**Executor** — carries out approved actions (writing logs, updating records). Only acts after supervisor approval.

---

## Supervisor pattern

The supervisor is the most common coordination pattern. One agent (the supervisor) manages a team of workers. It receives the user query, delegates to the right worker(s), collects results, and synthesises a final answer.

```
User query → Supervisor
    ├── Researcher (gathers data)
    ├── Analyst (interprets data)
    └── Critic (reviews draft)
         ↓
Supervisor → Final answer
```

```python
async def supervisor(query: str) -> str:
    research = await researcher.run(query)

    if research.confidence < 0.7:
        research = await researcher.run(query, hint="Try broader search")

    critique = await critic.review(research.findings)

    if critique.approved:
        return format_answer(research.findings, critique.notes)
    else:
        # Ask researcher to revise based on critique
        revised = await researcher.revise(research, critique.feedback)
        return format_answer(revised.findings)
```

The supervisor has control flow logic — retries, critique loops, formatting. Worker agents are stateless functions that take input and return output.

---

## Debate pattern

For high-stakes decisions (mission abort, system shutdown), you want multiple perspectives. In the debate pattern, two or more agents argue opposing positions and a judge synthesises.

```python
async def debate(question: str, rounds: int = 2) -> str:
    positions = []
    for agent in [optimist, pessimist]:
        position = await agent.argue(question)
        positions.append(position)

    for _ in range(rounds):
        for i, agent in enumerate([optimist, pessimist]):
            other = positions[1 - i]
            rebuttal = await agent.rebut(other)
            positions[i] = rebuttal

    return await judge.synthesise(positions)
```

Debate is expensive (many LLM calls) but produces more balanced analysis. Use it for decisions where a single perspective could be biased or incomplete.

---

## Swarm / handoff pattern

In the supervisor pattern a central agent decides who runs next. In the **swarm** pattern there is no central controller — the **active agent** decides whether to use a tool, answer the user, or **hand off** to a colleague. The handoff is itself a tool call (`transfer_to_engineering`), so the LLM decides when to transfer based on its system prompt and the conversation so far.

```
User query → Comms (decrypt_signal)
           → transfer_to_engineering   ← handoff
           → Engineering (check_reactor)
           → final answer
```

Each agent has a **scoped tool set** — comms can decrypt signals but not check the reactor; engineering can run diagnostics but not scan frequencies. Transfer tools are the only bridge between domains. This enforces least-privilege access and keeps each agent's context focused.

```python
def swarm_loop(query, client, start_dept="comms", max_hops=6):
    dept = start_dept
    messages = build_agent_messages(dept, query)
    chain = [dept]

    for hop in range(max_hops):
        response = run_agent_turn(dept, messages, client)
        if not function_calls(response):
            return response.output_text, chain

        tool_msgs, transfer = handle_tool_calls(response, dept)
        messages.extend(tool_msgs)
        if transfer:
            dept = transfer
            chain.append(dept)
```

Cap hops with `max_hops` — unbounded handoff chains can burn tokens and loop. Always log the chain so you can trace the path through agents after the fact.

---

## Spawning subagents

Every pattern so far uses a **fixed roster** — the router picks one of three agents you wrote, the swarm hands control between officers that existed at import time. A **subagent** is created on demand instead: the lead writes a brief, the child runs in **its own context window**, and only its report comes back.

```
                      ┌── navigation  (own context, own tools) ──┐
Question → Lead agent ├── engineering (own context, own tools) ──┤ → reconcile → merge → answer
                      └── science     (own context, own tools) ──┘
```

Routing picks a worker and gets control back. A handoff gives control away and never gets it back. Spawning gives away *work* and gets a *result* back. That is the distinction worth holding on to.

### Why spawn at all

The headline reason is not speed — it is **context isolation**. A researcher can make thirty tool calls and read 40k tokens of logs; the lead only ever sees its three-sentence report. The lead stays small, so it stays coherent across a long task.

Parallelism is the bonus. Three researchers that each take eight seconds finish in eight seconds, not twenty-four.

The price is that the child **cannot see the conversation**. A vague brief is the single most common failure in a spawning system: the child fills the gap with a guess, confidently, and the lead has no way to tell.

### Parallel fan-out

```python
async def fan_out(briefs, client, max_workers=3):
    limit = asyncio.Semaphore(max_workers)

    async def guarded(brief):
        async with limit:
            return await run_subagent(brief, client)

    settled = await asyncio.gather(
        *(guarded(brief) for brief in briefs),
        return_exceptions=True,
    )

    return [
        outcome if not isinstance(outcome, BaseException) else stub(brief, outcome)
        for brief, outcome in zip(briefs, settled, strict=True)
    ]
```

Three details carry their weight:

- **`return_exceptions=True`** — without it, one subagent raising cancels its siblings and you throw away work that had already finished.
- **A semaphore**, not an unbounded `gather`. Twenty concurrent subagents will hit rate limits and your bill at the same time.
- **Results aligned with the briefs.** Substitute a stub for a failure rather than dropping it, so finding *i* still matches tool call *i* when you feed the outputs back.

This is Module 8's `depends_on` wave scheduling with agents in place of steps — the same `asyncio.gather`, one level up.

### Subagents as tools

You do not have to decide the fan-out yourself. Give the lead a spawn tool and the **model** decides how many children to create and what each one is asked:

```python
SPAWN_TOOL = {
    "type": "function",
    "name": "spawn_researchers",
    "description": (
        "Research independent sub-questions, each in its own context window. "
        "Pass every brief in one call — they all run at the same time."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "briefs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "department": {"type": "string", "enum": DEPARTMENTS},
                        "task": {"type": "string", "description": "A self-contained brief."},
                    },
                    "required": ["department", "task"],
                },
            }
        },
        "required": ["briefs"],
    },
}

briefs = to_briefs(spawn_calls(response))         # the model wrote these
findings = await fan_out(briefs, client)           # you run them

messages.append({
    "type": "function_call_output",
    "call_id": call.call_id,
    "output": json.dumps([f.report.model_dump() for f in findings]),  # reports, not transcripts
})
```

This is the `Task` tool in Cursor and Claude Code: a subagent behind a tool schema.

Note the shape of the arguments. The obvious design is one call per child, relying on the model to emit several tool calls in a turn — but plenty of models reliably will not. They spawn one, read the report, spawn the next, and your parallel system is quietly serial while every log line still says "spawned". Putting the **list of briefs in one argument** makes the fan-out a single visible decision. Keep handling multiple calls per turn as well, merged into one `fan_out`, for the models that do batch.

Two guard rails: validate the `department` the model invented against your own list before spawning anything, and cap both the number of children per turn and the **depth** — a child holding a spawn tool will spawn grandchildren.

### Reconciling the results

Subagents disagree. Three strategies, in increasing cost:

1. **Deterministic merge** — dedupe identical claims, concatenate the rest, keep provenance. No model, no tokens.
2. **Structured reduce** — ask each child for a schema with comparable fields, then compare them in code.
3. **LLM synthesis** — a merge call that writes the final answer.

```python
class SubagentReport(BaseModel):
    claim: str
    evidence: list[str]
    storm_eta_hours: float | None    # comparable in code; `claim` is not
    confidence: float


def reconcile(findings):
    etas = {f.department: f.report.storm_eta_hours for f in findings
            if f.report.storm_eta_hours is not None}
    if len(etas) >= 2 and max(etas.values()) - min(etas.values()) >= 2:
        return [f"storm ETA disagrees: {etas}"]
    return []
```

The point of the numeric field is that **you can only check in code what you asked for as data**. A prose claim is unverifiable, so the schema carries the number separately.

Then hand the conflicts you found to the merger agent, explicitly. A model asked to merge "4 hours" and "9 hours" without being warned they clash will quietly average them to six and a half, and the answer will read perfectly reasonable. Told about the disagreement, it names it and picks a side.

Attach provenance in the **parent**, never in the child's schema — a subagent that reports its own department can misreport it. And log every worker that failed: a silently dropped subagent turns into an answer that is confidently incomplete.

Cost is the last thing to say out loud. Five subagents is five times the tokens for one times the wall clock. That is often a good trade, but it is a trade.

---

## Shared context and tools

Agents in a team often need to share data — the researcher's findings feed the critic, the supervisor's plan guides the executor. Two approaches:

**Shared message list** — all agents read from and write to a common message history. Simple but noisy — agents see each other's internal reasoning.

**Structured handoffs** — each agent receives a clean input and returns a clean output. The supervisor manages what goes where. More work to implement but much cleaner boundaries.

Tools can be shared or exclusive. The researcher gets RAG tools; the executor gets write tools; the critic gets neither (it only evaluates). Restricting tool access per role is a safety measure — the critic cannot accidentally modify data.

---

## Consensus and conflict resolution

When multiple agents provide answers, they may disagree. A consensus mechanism resolves conflicts deterministically:

**Majority vote** — ask N agents the same question, take the most common answer. Simple and robust for classification tasks.

**Weighted ranking** — each agent scores options, weights are summed, highest total wins.

**Tie-breaking** — when votes are equal, fall back to a designated authority (the supervisor) or use the first response.

```python
def consensus(proposals: list[str]) -> str:
    votes = Counter(proposals)
    winner, count = votes.most_common(1)[0]

    if count > len(proposals) // 2:
        return winner

    # Tie: supervisor breaks it
    return supervisor_tiebreak(proposals)
```

Always log dissent — if an agent disagrees with the consensus, that disagreement may contain a warning worth reviewing later.

---

## Summary

- **One agent until you can justify another.** If one prompt can do it, one agent should do it.
- **Roles stay narrow.** Router, specialist, critic, supervisor. Overlap means duplicate work.
- **Pick one coordination pattern.** Supervisor, swarm, debate, or consensus — and stick to it.
- **Scope tools and log the trace.** The critic should not have write access. Keep the whole conversation, including dissent.
- **A subagent is a context window, not a job title.** Spawn for isolation, cap the workers and the depth, and never let a merge average a conflict away.

---

## Demos

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python module-09-multi-agent/demo/demo.py

# Option B - uv (no activation needed):
uv run python module-09-multi-agent/demo/demo.py
```

Menu:
1. **Route** — one question, one specialist
2. **Critic** — review and revise
3. **Debate** — advocate, skeptic, judge
4. **Consensus** — three departments vote
5. **Swarm** — handoffs with scoped tools
6. **Subagents** — spawned on demand, run at once, reports reconciled

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-router-agent`](exercises/01-router-agent/) | Build specialist agents (medical, tactical, comms) and an LLM-powered router that classifies queries and dispatches to the right specialist. |
| [`exercises/02-supervisor-critic`](exercises/02-supervisor-critic/) | Supervisor orchestrates specialists + critic with a revision loop for quality control. |
| [`exercises/03-consensus`](exercises/03-consensus/) | Debate pattern, judge synthesis, and consensus voting across multiple agents. |
| [`exercises/04-swarm-tools`](exercises/04-swarm-tools/) | Swarm handoffs: each agent has scoped ship tools and passes control via `transfer_to_*`. |
| [`exercises/05-subagents`](exercises/05-subagents/) | Spawn subagents from a `spawn_researcher` tool, fan them out concurrently, then reconcile conflicting reports before merging. |

Run tests per exercise (each folder has its own `test_start.py`):

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pytest module-09-multi-agent/exercises/01-router-agent/ -v
pytest module-09-multi-agent/exercises/05-subagents/ -v

# Option B - uv (no activation needed):
uv run --extra dev pytest module-09-multi-agent/exercises/01-router-agent/ -v
uv run --extra dev pytest module-09-multi-agent/exercises/05-subagents/ -v
```

## Slides

From repo root: `pnpm slides:09`, or `cd module-09-multi-agent/slides && pnpm dev`.

## Reference

### Frameworks and documentation

- [LangGraph — Multi-Agent](https://langchain-ai.github.io/langgraph/concepts/multi_agent/)
- [OpenAI Agents SDK — handoffs](https://openai.github.io/openai-agents-python/handoffs/) — the production successor to the experimental Swarm library; handoffs are the swarm pattern from exercise 04
- [OpenAI Agents SDK — agents as tools](https://openai.github.io/openai-agents-python/tools/) — `agent.as_tool()`: the spawn-as-tool pattern from exercise 05, with the framework doing the plumbing
- [LangGraph — map-reduce with `Send`](https://langchain-ai.github.io/langgraph/how-tos/map-reduce/) — fanning out a dynamic number of workers and gathering their results back into state
- [Anthropic — How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — a production lead/subagent system: brief quality, parallel fan-out, and the token cost they measured
- [Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/) — successor to AutoGen (now archived)

### Academic papers

**Surveys and foundations**

- [The Rise and Potential of Large Language Model Based Agents (Xi et al. 2023)](https://arxiv.org/abs/2309.07864) — taxonomy of LLM agents, planning, memory, and multi-agent collaboration.
- [ReAct: Synergizing Reasoning and Acting in Language Models (Yao et al. 2022)](https://arxiv.org/abs/2210.03629) — tool-using agents; basis for specialist agents with scoped tools (see also Module 8).

**Multi-agent frameworks and role specialisation**

- [AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation (Wu et al. 2023)](https://arxiv.org/abs/2308.08155) — conversational multi-agent orchestration and human-in-the-loop patterns.
- [CAMEL: Communicative Agents for “Mind” Exploration (Li et al. 2023)](https://arxiv.org/abs/2303.17760) — role-playing agents with structured handoffs between specialised roles.
- [MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework (Hong et al. 2023)](https://arxiv.org/abs/2308.00352) — standardised operating procedures and division of labour across agents.
- [ChatDev: Communicative Agents for Software Development (Qian et al. 2023)](https://arxiv.org/abs/2307.07924) — chain-style collaboration (design → code → review) akin to supervisor pipelines.
- [Least-to-Most Prompting Enables Complex Reasoning (Zhou et al. 2022)](https://arxiv.org/abs/2205.10625) — decomposing a problem into independently solvable sub-problems; the brief-writing half of spawning subagents.

**Debate, critique, and consensus**

- [Improving Factuality and Reasoning in Language Models through Multiagent Debate (Du et al. 2023)](https://arxiv.org/abs/2305.14325) — adversarial agents and a judge; motivates the debate pattern in Exercise 03.
- [Reflexion: Language Agents with Verbal Reinforcement Learning (Shinn et al. 2023)](https://arxiv.org/abs/2303.11366) — self-critique and revision loops; close to supervisor–critic pipelines.
- [Self-Consistency Improves Chain of Thought Reasoning in Language Models (Wang et al. 2022)](https://arxiv.org/abs/2203.11171) — sampling multiple answers and aggregating; theoretical basis for majority voting / consensus.

**Agent societies and emergent coordination**

- [Generative Agents: Interactive Simulacra of Human Behavior (Park et al. 2023)](https://arxiv.org/abs/2304.03442) — many agents sharing an environment and memory; useful context for swarm-style peer coordination.

**Failure modes**

- [Why Do Multi-Agent LLM Systems Fail? (Cemri et al. 2025)](https://arxiv.org/abs/2503.13657) — a taxonomy of 14 failure modes across specification, inter-agent misalignment, and verification; the empirical case for "one agent until you can justify another".
