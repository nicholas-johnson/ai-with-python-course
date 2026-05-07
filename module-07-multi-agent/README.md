# Module 7 — Multi-Agent Systems

**Many minds, one mission.** Sometimes a single agent is enough; sometimes the Pathfinder needs a router, specialists, and a critic working in concert. This module explores when multi-agent architectures help or hurt, common roles and coordination patterns, shared context and tools, and how to resolve disagreement.

## Learning goals

- Decide **when multi-agent** designs are worth the latency and operational complexity.
- Model **roles** (router, researcher, coder, critic, executor) and **coordination patterns** (supervisor, swarm, debate, blackboard, task queue).
- Share **context and tools** safely across agents and apply **conflict resolution** / consensus strategies.

## Instructor notes

- **Agent roles** (`demo/01_agent_roles.py`): splitting responsibilities without duplicating every capability.
- **Supervisor pattern** (`demo/02_supervisor_pattern.py`): a lead agent delegates and merges results.
- **Debate pattern** (`demo/03_debate_pattern.py`): opposing views before a decision — useful for high-stakes planning.

## Demos

```bash
python module-07-multi-agent/demo/01_agent_roles.py
python module-07-multi-agent/demo/02_supervisor_pattern.py
python module-07-multi-agent/demo/03_debate_pattern.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-router-agent`](exercises/01-router-agent/) | Route crew queries to specialist agents (navigation, engineering, science). |
| [`exercises/02-research-team`](exercises/02-research-team/) | Supervisor coordinates a researcher and a critic for mission briefings. |
| [`exercises/03-consensus`](exercises/03-consensus/) | Multiple agents propose answers; aggregate or vote on the best response. |

Run tests for this module:

```bash
pytest module-07-multi-agent/
```

## Slides

From repo root: `pnpm slides:07`, or `cd module-07-multi-agent/slides && pnpm dev`.

## Reference

- [LangGraph documentation](https://langchain-ai.github.io/langgraph/)
- [AutoGen (Microsoft)](https://microsoft.github.io/autogen/)
- [LangGraph multi-agent examples](https://langchain-ai.github.io/langgraph/)
