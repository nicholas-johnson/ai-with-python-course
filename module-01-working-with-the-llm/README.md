# Module 1 — Working with the LLM

> Time to talk to the model. After building a solid Python foundation, the Pathfinder AI needs a voice. This module is your "hello world" with LLMs — making real API calls, building a CLI chat interface where crew members type questions and see answers stream back token by token, and adding persistence so conversations survive between watches. By the end of this module you have a working chatbot you can run from the terminal.

## Learning goals

- Call the **LLM chat-completion API** directly (message roles, parameters, responses).
- Build a **CLI chat loop** with conversation history.
- **Stream responses** token by token for real-time output.
- Add **persistence** so conversations survive restarts.
- Apply **prompting patterns** that hold up in production (system prompts, structured outputs).

---

## The chat loop

The core pattern is a function that calls the OpenAI API:

```python
from openai import OpenAI

client = OpenAI()

def chat(client, messages):
    response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return response.choices[0].message.content
```

The model sees the full context every time — that is how it "remembers" the conversation. The catch is that the history grows with every turn. When it exceeds the model's context window you need to truncate or summarise (covered in Module 7).

Wrap this in an input loop:

```python
messages = [{"role": "system", "content": "You are the DSS Pathfinder ship AI."}]

while True:
    user_input = input("You: ").strip()
    if user_input.lower() in ("quit", "exit"):
        break
    messages.append({"role": "user", "content": user_input})
    response = chat(client, messages)
    messages.append({"role": "assistant", "content": response})
    print(f"AI: {response}")
```

---

## Streaming responses

With streaming, the first token appears in ~200ms and words flow in as they are generated. The total time is the same, but perceived latency drops dramatically.

```python
def stream_response(client, messages):
    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=messages, stream=True,
    )
    tokens = []
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            sys.stdout.write(content)
            sys.stdout.flush()
            tokens.append(content)
    print()
    return "".join(tokens)
```

Each chunk contains a `delta` with a fragment of the response. Print it immediately and the user sees words appear as they are generated. Streaming also lets you show **tool calls in progress** in later modules — the user sees "Querying crew database..." before the final answer.

---

## SSE streaming with FastAPI

For web applications, Server-Sent Events (SSE) are the simplest way to stream from a server to a browser. They use plain HTTP (no WebSocket upgrade), work through proxies and CDNs, and are natively supported by `EventSource` in JavaScript.

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

## Conversation persistence

A chat application needs to store conversation history so it survives restarts. The simplest approach is writing the messages list to a JSON file:

```python
import json
from pathlib import Path

def save_session(filepath: Path, messages: list[dict]) -> None:
    filepath.write_text(json.dumps(messages, indent=2))

def load_session(filepath: Path) -> list[dict]:
    if not filepath.exists():
        return [{"role": "system", "content": system_prompt}]
    return json.loads(filepath.read_text())
```

For production systems you would use Redis or Postgres, but file-based persistence is a solid start. The key insight is to **code to an interface** — define a `SessionBackend` Protocol and swap implementations without changing other code.

---

## Slash commands

A well-designed CLI chat supports commands alongside conversation. Prefix commands with `/` so they are easy to distinguish from chat messages:

```python
if user_input.startswith("/"):
    handle_command(user_input, messages, filepath)
else:
    # send to LLM
```

Common commands: `/clear` (reset history), `/history` (show conversation), `/save` and `/load` (persistence), `/help` (list commands).

---

## Tool call UX

When the agent calls a tool mid-conversation, the user should see what is happening. Stream a `tool_call` event with the tool name and arguments, then a `tool_result` event with the outcome, before the final answer resumes. This makes the AI transparent — the crew can see it querying the crew database, not just producing an answer from thin air.

Citations work the same way: when the answer references data from a tool call, link it back to the source so the user can verify.

---

## Field rules

- **Stream by default.** Waiting 5 seconds for a response feels broken.
- **Persist conversations.** Users expect to pick up where they left off.
- **Show your work.** Tool calls in the stream let users see what the AI is doing.

---

## Demos

```bash
python module-01-working-with-the-llm/demo/01_chat_cli.py
python module-01-working-with-the-llm/demo/02_api_backend.py
python module-01-working-with-the-llm/demo/03_session_storage.py
```

## Exercises

The exercises chain — each one builds on the previous. Run them with `python start.py` for an interactive chat, or use `pytest` to validate.

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-first-chat`](exercises/01-first-chat/) | Make your first LLM API call and build an input loop. |
| [`exercises/02-streaming`](exercises/02-streaming/) | Upgrade the chat to stream responses token by token. |
| [`exercises/03-chat-app`](exercises/03-chat-app/) | Add slash commands and file persistence. |

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
