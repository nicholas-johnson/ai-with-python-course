# Module 3 — Working with the LLM

**Time to talk to the model.** This module builds your first real integration with an LLM — calling chat-completion APIs, streaming responses, shaping prompts that produce reliable outputs, and managing session history so conversations persist across interactions.

## Learning goals

- Call the **LLM chat-completion API** directly (message roles, parameters, streaming).
- Build a **CLI chat loop** with conversation history.
- Create a **FastAPI streaming endpoint** using Server-Sent Events (SSE).
- Implement **session storage**: in-memory first, then file-based.
- Apply **prompting patterns** that hold up in production (structured outputs, grounding).

## Instructor notes

- **Chat CLI** (demo `01_chat_cli.py`): readline-based input loop, conversation history in a list, streaming token output to the terminal.
- **API backend** (demo `02_api_backend.py`): FastAPI endpoint that accepts a chat message, streams the response via SSE, and includes tool-call events in the stream.
- **Session storage** (demo `03_session_storage.py`): the progression from in-memory dict to file-based JSON to the concept of pluggable backends (Redis/Postgres mentioned but not implemented here).

## Demos

```bash
python module-03-working-with-the-llm/demo/01_chat_cli.py
python module-03-working-with-the-llm/demo/02_api_backend.py
python module-03-working-with-the-llm/demo/03_session_storage.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-chat-loop`](exercises/01-chat-loop/) | Build a CLI chatbot with conversation history. |
| [`exercises/02-streaming-api`](exercises/02-streaming-api/) | FastAPI streaming endpoint with SSE. |
| [`exercises/03-session-manager`](exercises/03-session-manager/) | Pluggable session backend: in-memory then file-based. |

Run tests for this module:

```bash
pytest module-03-working-with-the-llm/
```

## Slides

From repo root: `pnpm slides:03`, or `cd module-03-working-with-the-llm/slides && pnpm dev`.

## Reference

- [FastAPI streaming](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [sse-starlette](https://github.com/sysid/sse-starlette)
