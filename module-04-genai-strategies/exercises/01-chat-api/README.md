# Exercise 1: Streaming Chat API

## Recap

FastAPI makes it straightforward to build an API that streams tokens from the LLM to the browser in real time. The key ingredients:

- **Server-Sent Events (SSE)** -- a one-way channel from server to client over HTTP. The `sse-starlette` package provides `EventSourceResponse` which wraps an async generator into the correct wire format.
- **OpenAI streaming** -- pass `stream=True` to `client.chat.completions.create()` and iterate over chunks:

```python
stream = client.chat.completions.create(
    model="gpt-4o-mini", messages=messages, stream=True
)
for chunk in stream:
    token = chunk.choices[0].delta.content
    if token:
        print(token, end="", flush=True)
```

- **CORS middleware** -- browsers enforce same-origin policy. During development the frontend runs on a different port, so the backend needs `CORSMiddleware` with `allow_origins=["*"]`.

## What you build

A FastAPI app in **`start.py`** with two endpoints:

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Returns `{"status": "ok"}` |
| `/chat` | POST | Accepts `{"messages": [...]}`, streams the response as SSE |

The SSE stream emits two event types:

| Event | Payload | When |
|---|---|---|
| `token` | `{"token": "Hello"}` | Each incremental piece of text |
| `done` | `{"role": "assistant", "content": "..."}` | The complete assistant message at the end |

## Step-by-step

### 1. Create the FastAPI app

Open `start.py`. Set up a FastAPI instance and add CORS middleware:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
```

### 2. Add the health endpoint

```python
@app.get("/health")
async def health():
    return {"status": "ok"}
```

### 3. Define the request model

Use Pydantic to validate the incoming chat request:

```python
from pydantic import BaseModel

class ChatRequest(BaseModel):
    messages: list[dict]
```

### 4. Build the streaming chat endpoint

Create `POST /chat` that:

1. Initialises the OpenAI client
2. Calls `client.chat.completions.create(stream=True, ...)`
3. Iterates over the stream, collecting tokens
4. Yields SSE events for each token
5. Yields a final `done` event with the complete message

Wrap the generator with `EventSourceResponse`:

```python
from sse_starlette.sse import EventSourceResponse
import json

@app.post("/chat")
async def chat(req: ChatRequest):
    async def generate():
        # TODO: stream from OpenAI and yield SSE events
        pass
    return EventSourceResponse(generate())
```

**Hint:** Each SSE event needs a `dict` with `"event"` and `"data"` keys:

```python
yield {"event": "token", "data": json.dumps({"token": text})}
```

### 5. Run and test

Start the server:

```bash
uvicorn start:app --reload --port 8000
```

Test with curl:

```bash
curl -N -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello!"}]}'
```

You should see SSE events streaming back.

## Try it

Start the backend, then start the frontend:

```bash
# Terminal 1 -- backend
cd module-04-genai-strategies/exercises/01-chat-api
uvicorn start:app --reload --port 8000

# Terminal 2 -- frontend
cd module-04-genai-strategies/frontend
pnpm dev
```

Open the browser, type a message, and watch it stream in.

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- `/health` returns 200 with the correct JSON
- `/chat` returns a valid SSE stream with `token` and `done` events

## Stretch goals

- Add a `model` field to `ChatRequest` so the user can pick `gpt-4o-mini` vs `gpt-4o`
- Add a system message that gives the assistant a research-focused personality
- Handle the case where `OPENAI_API_KEY` is not set with a friendly error
