# Exercise 03 — ReAct Loop

**Mission briefing:** Implement a minimal **ReAct** loop: the agent **thinks** (reason string), **acts** by calling a named tool from a registry, then **observes** the tool output until a stop condition (max steps or `finish` tool).

## Objectives

1. Define a small `Tool` registry: `lookup_star_chart`, `read_sensor` (stubs OK).
2. `react_step(state) -> state` — append thought, action, observation to state.
3. `run_react(query, max_steps=5) -> list[dict]` — full trace.

## Run the tests

```bash
pytest module-07-agent-memory/exercises/03-react-loop/test_start.py -v
```
