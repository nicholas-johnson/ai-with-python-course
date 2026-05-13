# Module 1 — Working with the LLM

> Time to talk to the model. After building a solid Python foundation, the Pathfinder AI needs a voice. This module is your "hello world" with LLMs — making real API calls, building a CLI chat interface where crew members type questions and see answers stream back token by token, an HTTP API so the bridge console can connect, and session storage so conversations survive between watches. By the end of this module you have a working chatbot.

## Learning goals

- Call the **LLM chat-completion API** directly (message roles, parameters, streaming).
- Build a **CLI chat loop** with conversation history.
- Create a **FastAPI streaming endpoint** using Server-Sent Events (SSE).
- Implement **session storage**: in-memory first, then file-based.
- Apply **prompting patterns** that hold up in production (structured outputs, grounding).

---

## The chat loop

A chatbot is a while-loop that maintains a growing list of messages. Each turn appends the user's input, sends the full history to the model, and appends the response.

```python
class ChatBot:
    def __init__(self, llm, system_prompt):
        self.messages = [{"role": "system", "content": system_prompt}]

    def chat(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})
        response = self.llm.chat(self.messages)
        self.messages.append({"role": "assistant", "content": response})
        return response
```

The model sees the full context every time — that is how it "remembers" the conversation. The catch is that the history grows with every turn. When it exceeds the model's context window you need to truncate or summarise (covered in Module 7).

For a CLI interface, wrap this in an input loop with `readline`:

```python
while True:
    user_input = input("You> ").strip()
    if user_input.lower() in ("quit", "exit"):
        break
    print("AI>", bot.chat(user_input))
```

---

## Why streaming matters

Without streaming, the user types a question and stares at a blank screen for 2-5 seconds while the model generates the full response. With streaming, the first token appears in ~200ms and words flow in as they are generated. The total time is the same, but perceived latency drops dramatically.

Streaming also lets you show **tool calls in progress** — the user sees "Querying crew database..." before the final answer appears. Transparency builds trust.

---

## SSE streaming with FastAPI

Server-Sent Events (SSE) are the simplest way to stream from a server to a browser. They use plain HTTP (no WebSocket upgrade), work through proxies and CDNs, and are natively supported by `EventSource` in JavaScript.

```python
from sse_starlette.sse import EventSourceResponse

@app.post("/chat")
async def chat(request: ChatRequest):
    async def generate():
        yield {"event": "session", "data": json.dumps({"session_id": sid})}
        async for token in llm.stream(messages):
            yield {"event": "token", "data": json.dumps({"token": token})}
        yield {"event": "done", "data": json.dumps({"full_response": text})}

    return EventSourceResponse(generate())
```

Each `yield` sends an SSE event to the client immediately. The event structure is up to you — here we use `session` (metadata), `token` (incremental text), and `done` (final state). For tool calls, add `tool_call` and `tool_result` events so the UI can show what the agent is doing.

---

## Session storage — in-memory, then persistent

A chat application needs to store conversation history between HTTP requests. The simplest backend is an in-memory dict — fast, but lost on server restart. A file backend survives restarts but does not scale to multiple server instances. In production you would use Redis or Postgres.

The key insight is to **code to an interface**, not to a specific backend. Define a `SessionBackend` Protocol, then swap implementations without changing any other code:

```python
class SessionBackend(Protocol):
    def load(self, session_id: str) -> list[dict]: ...
    def save(self, session_id: str, messages: list[dict]) -> None: ...
    def exists(self, session_id: str) -> bool: ...

class SessionManager:
    def __init__(self, backend: SessionBackend):
        self.backend = backend
```

| In-memory | File / DB |
| --------- | --------- |
| Fast: plain dict lookup | Survives restarts |
| Lost on server restart | Shareable across instances |
| Fine for development | Slightly slower (disk/network I/O) |
| No shared state between instances | Production-ready with Redis/Postgres |

The `InMemoryBackend` stores sessions in a dict. The `FileBackend` writes each session as a JSON file in a directory. Both implement the same three methods, so `SessionManager` works identically with either one.

```python
# Swap backends without touching the rest of the codebase
mgr = SessionManager(InMemoryBackend())
mgr = SessionManager(FileBackend(Path("./sessions")))
```

---

## Tool call UX

When the agent calls a tool mid-conversation, the user should see what is happening. Stream a `tool_call` event with the tool name and arguments, then a `tool_result` event with the outcome, before the final answer resumes. This makes the AI transparent — the crew can see it querying the crew database, not just producing an answer from thin air.

Citations work the same way: when the answer references data from a tool call, link it back to the source so the user can verify.

---

## Field rules

- **Stream by default.** Waiting 5 seconds for a response feels broken.
- **Sessions are backend-agnostic.** Code to Protocol, not to dict or file.
- **Show your work.** Tool calls in the stream let users see what the AI is doing.

---

## Demos

```bash
python module-01-working-with-the-llm/demo/01_chat_cli.py
python module-01-working-with-the-llm/demo/02_api_backend.py
python module-01-working-with-the-llm/demo/03_session_storage.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-chat-loop`](exercises/01-chat-loop/) | Build a CLI chatbot with conversation history. |
| [`exercises/02-streaming-api`](exercises/02-streaming-api/) | FastAPI streaming endpoint with SSE. |
| [`exercises/03-session-manager`](exercises/03-session-manager/) | Pluggable session backend: in-memory then file-based. |

Run tests for this module:

```bash
pytest module-01-working-with-the-llm/
```

## Slides

From repo root: `pnpm slides:01`, or `cd module-01-working-with-the-llm/slides && pnpm dev`.

## Reference

- [OpenAI API — Chat completions](https://platform.openai.com/docs/guides/text-generation)
- [FastAPI streaming](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [sse-starlette](https://github.com/sysid/sse-starlette)
