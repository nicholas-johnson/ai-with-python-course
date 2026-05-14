# Exercise 02 — Tool Agent

**Mission briefing:** Take the ship tools you built in module 05 (sensor read, crew lookup, log query) and wrap them as **LangChain tools**. Wire them into an **AgentExecutor** so the model can call them in a loop — just like your hand-rolled agent, but using the framework.

## Objectives

1. Define LangChain `@tool` wrappers for at least two ship tools.
2. Create an agent with `create_tool_calling_agent` and `AgentExecutor`.
3. Invoke the agent with a natural-language query and verify it calls the right tool.

## Run the tests

```bash
pytest module-10-langchain/exercises/02-tool-agent/test_start.py -v
```
