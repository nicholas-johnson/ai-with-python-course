# Module 9 — Multi-Agent Systems

> One agent is useful. A crew of agents — each with a speciality, coordinated by a supervisor or handing off peer-to-peer — can tackle problems no single model could handle alone. The Pathfinder's bridge crew is the model: a commander routes queries, a science officer researches, an engineer inspects systems, and a critic reviews the work before it reaches the crew. In this module you design multi-agent architectures, build coordination patterns (supervisor, swarm, debate, consensus), and learn when multiple agents are worth the complexity.

## Learning goals

- Know **when to use** multi-agent systems (and when a single agent is better).
- Define **agent roles**: router, researcher, critic, supervisor, executor.
- Implement **coordination patterns**: supervisor, swarm, debate, blackboard, task queue.
- Share **context and tools** between agents safely.
- Build **conflict resolution** and consensus mechanisms.

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
        msg = run_agent_turn(dept, messages, client)
        if not msg.tool_calls:
            return msg.content, chain

        tool_msgs, transfer = handle_tool_calls(msg, dept)
        messages.extend(tool_msgs)
        if transfer:
            dept = transfer
            chain.append(dept)
```

Cap hops with `max_hops` — unbounded handoff chains can burn tokens and loop. Always log the chain so you can trace the path through agents after the fact.

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

## Field rules

- **Start with one agent.** Only add more when a single agent demonstrably cannot handle the task.
- **Define roles clearly.** Overlapping responsibilities cause duplicate work and conflicting answers.
- **Restrict tool access per role.** The critic should not have write access.
- **Log dissent.** Minority opinions may contain early warnings.

---

## Demos

```bash
python module-09-multi-agent/demo/demo.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-router-agent`](exercises/01-router-agent/) | Build specialist agents (medical, tactical, comms) and an LLM-powered router that classifies queries and dispatches to the right specialist. |
| [`exercises/02-supervisor-critic`](exercises/02-supervisor-critic/) | Supervisor orchestrates specialists + critic with a revision loop for quality control. |
| [`exercises/03-consensus`](exercises/03-consensus/) | Debate pattern, judge synthesis, and consensus voting across multiple agents. |
| [`exercises/04-swarm-tools`](exercises/04-swarm-tools/) | Swarm handoffs: each agent has scoped ship tools and passes control via `transfer_to_*`. |

Run tests per exercise (each folder has its own `test_start.py`):

```bash
pytest module-09-multi-agent/exercises/01-router-agent/ -v
pytest module-09-multi-agent/exercises/04-swarm-tools/ -v
```

## Slides

From repo root: `pnpm slides:09`, or `cd module-09-multi-agent/slides && pnpm dev`.

## Reference

### Frameworks and documentation

- [LangGraph — Multi-Agent](https://langchain-ai.github.io/langgraph/concepts/multi_agent/)
- [OpenAI Swarm (experimental)](https://github.com/openai/swarm)
- [AutoGen](https://microsoft.github.io/autogen/)

### Academic papers

**Surveys and foundations**

- [The Rise and Potential of Large Language Model Based Agents (Xi et al. 2023)](https://arxiv.org/abs/2309.07864) — taxonomy of LLM agents, planning, memory, and multi-agent collaboration.
- [ReAct: Synergizing Reasoning and Acting in Language Models (Yao et al. 2022)](https://arxiv.org/abs/2210.03629) — tool-using agents; basis for specialist agents with scoped tools (see also Module 8).

**Multi-agent frameworks and role specialisation**

- [AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation (Wu et al. 2023)](https://arxiv.org/abs/2308.08155) — conversational multi-agent orchestration and human-in-the-loop patterns.
- [CAMEL: Communicative Agents for “Mind” Exploration (Li et al. 2023)](https://arxiv.org/abs/2303.17760) — role-playing agents with structured handoffs between specialised roles.
- [MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework (Hong et al. 2023)](https://arxiv.org/abs/2308.00352) — standardised operating procedures and division of labour across agents.
- [ChatDev: Communicative Agents for Software Development (Qian et al. 2023)](https://arxiv.org/abs/2307.07924) — chain-style collaboration (design → code → review) akin to supervisor pipelines.

**Debate, critique, and consensus**

- [Improving Factuality and Reasoning in Language Models through Multiagent Debate (Du et al. 2023)](https://arxiv.org/abs/2305.14325) — adversarial agents and a judge; motivates the debate pattern in Exercise 03.
- [Reflexion: Language Agents with Verbal Reinforcement Learning (Shinn et al. 2023)](https://arxiv.org/abs/2303.11366) — self-critique and revision loops; close to supervisor–critic pipelines.
- [Self-Consistency Improves Chain of Thought Reasoning in Language Models (Wang et al. 2022)](https://arxiv.org/abs/2203.11171) — sampling multiple answers and aggregating; theoretical basis for majority voting / consensus.

**Agent societies and emergent coordination**

- [Generative Agents: Interactive Simulacra of Human Behavior (Park et al. 2023)](https://arxiv.org/abs/2304.03442) — many agents sharing an environment and memory; useful context for swarm-style peer coordination.
