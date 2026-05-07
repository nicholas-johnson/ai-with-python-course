# Module 8 — Agent Memory + Workflows

**The ship remembers.** Useful agents need **session context**, durable **user preferences**, and policies for **forgetting**. This module connects short-term and long-term memory, summarisation, decay, and workflow patterns: ReAct, plan-and-execute, and tool routing on the DSS Pathfinder.

## Learning goals

- Implement **short-term memory** (conversation/session) separate from **long-term** profile or notes.
- Apply **summarisation** to fit context limits; model **decay** and explicit **"do not remember"** controls.
- Compare **workflow patterns**: ReAct, plan-and-execute, and tool routing for multi-step missions.

## Topics

- Session buffers vs persistent stores; privacy and retention.
- Summarising long threads; forgetting and TTL; user overrides.
- ReAct loop (reason → act → observe); planning vs reactive tool use.

## Demos

```bash
python module-08-agent-memory/demo/01_memory_types.py
python module-08-agent-memory/demo/02_summarisation.py
python module-08-agent-memory/demo/03_workflow_patterns.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-memory-store`](exercises/01-memory-store/) | **Short-term** and **long-term** memory with **decay**. |
| [`exercises/02-conversation-summary`](exercises/02-conversation-summary/) | **Summarise** long conversations to fit a token budget. |
| [`exercises/03-react-loop`](exercises/03-react-loop/) | Implement **ReAct**: Reason → Act → Observe. |

Run tests for this module:

```bash
pytest module-08-agent-memory/
```

## Slides

From repo root: `pnpm slides:08`, or `cd module-08-agent-memory/slides && pnpm dev`.

## Reference

- [LangGraph — memory concepts](https://langchain-ai.github.io/langgraph/concepts/memory/)
- [ReAct paper (arXiv)](https://arxiv.org/abs/2210.03629)
- [Anthropic — long context tips](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips)
