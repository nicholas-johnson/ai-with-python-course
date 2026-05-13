# Exercise 01 — Tool-Calling Agent

**Mission briefing:** The Pathfinder AI can hold a conversation, but it cannot *do* anything yet. In this exercise you give it hands — tool definitions that tell the model what actions are available, handler functions that execute them, and a loop that keeps calling the model until it has a final answer.

## Objectives

1. Define tool schemas in OpenAI format (`TOOLS` list).
2. Implement handler functions that return data (`TOOL_HANDLERS` dict).
3. Implement `run_agent(client, question, max_steps)` — the tool-calling loop:
   - Call `client.chat.completions.create()` with `tools=TOOLS`.
   - If the model returns `tool_calls`, execute each one and feed the result back.
   - If the model returns text content, return it as the final answer.
   - Stop after `max_steps` to prevent runaway loops.
4. Return an `AgentResult` with the answer, tools used, and step count.

## Try it

```bash
python start.py
```

Type a question like *"How many crew in the science department?"* or *"What's the warp drive status?"* and watch the agent call tools and answer.

## Run the tests

```bash
pytest module-02-agent-core/exercises/01-tool-calling-agent/test_start.py -v
```
