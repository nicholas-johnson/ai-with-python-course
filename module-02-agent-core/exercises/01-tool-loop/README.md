# Exercise 01 — Tool Loop

**Mission briefing:** The Pathfinder needs a core agent loop — the engine that drives every AI conversation. Given a user question, the loop asks the LLM for a response. If the LLM wants to call a tool, the loop executes it and feeds the result back. The loop repeats until the LLM produces a final text answer.

## Objectives

1. Implement `Message` and `ToolCall` dataclasses to represent conversation state.
2. Implement `run_tool_loop(llm, tools, user_input, max_steps)`:
   - Build an initial message list (system + user).
   - Call the LLM. If it returns tool calls, execute each tool and append the result.
   - If it returns content with no tool calls, return that as the final answer.
   - Respect `max_steps` to prevent infinite loops.
3. Return a `LoopResult` with the final answer, list of tool calls made, and step count.

## Run the tests

```bash
pytest module-02-agent-core/exercises/01-tool-loop/test_start.py -v
```
