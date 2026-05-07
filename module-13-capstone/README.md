# Module 13 — Capstone Project

**All systems integrated.** The capstone ties together everything the course built: a conversational agent for the DSS Pathfinder with retrieval, an MCP tool suite, and a multi-agent workflow for complex missions. You will walk through architecture, demo scenarios, tests, and a checklist for extending the system after class.

## Learning goals

- Ship a **full agentic application**: chat UI or CLI, RAG over ship knowledge, MCP tools, and a coordinated multi-agent path for hard questions.
- Practice **demo scenarios** that show value to mission ops and **integration tests** that guard regressions.
- Document **extension points** so future you (or your crew) can add tools, data sources, and policies safely.

## Instructor notes

- **Architecture overview** (`demo/01_architecture_overview.py`): components, data flow, and trust boundaries on the Pathfinder stack.
- **Demo scenario** (`demo/02_demo_scenario.py`): scripted walkthrough — e.g. crew question → RAG + tools → supervisor handoff.

## Demos

```bash
python module-13-capstone/demo/01_architecture_overview.py
python module-13-capstone/demo/02_demo_scenario.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-capstone-app`](exercises/01-capstone-app/) | Build the integrated Pathfinder agentic app (chat + RAG + MCP + multi-agent). |
| [`exercises/02-test-and-extend`](exercises/02-test-and-extend/) | Add integration tests and document how to extend tools, retrieval, and workflows. |

Run tests for this module:

```bash
pytest module-13-capstone/
```

## Slides

From repo root: `pnpm slides:13`, or `cd module-13-capstone/slides && pnpm dev`.

## Reference

- [Model Context Protocol spec](https://modelcontextprotocol.io/)
- [LangChain / LangGraph docs](https://python.langchain.com/docs/)
- [OpenAI Agents SDK (optional patterns)](https://openai.github.io/openai-agents-python/)
