# Exercise 4: LangServe API

> **Scenario:** Hands-on work uses the **CSS Horizon** cargo survey vessel. Module demo 04 uses the **DSS Pathfinder** — same LangServe pattern, different vessel name in the prompt.

## Recap

You built an LCEL classifier in exercise 01. **LangServe** turns that Runnable into a REST API on FastAPI with one function:

```python
from langserve import add_routes

add_routes(app, chain, path="/classify")
```

LangServe registers `/classify/invoke`, `/classify/stream`, `/classify/batch`, and `/classify/playground` automatically.

## What you build

A FastAPI app in **`start.py`** that:

| Piece | Detail |
|-------|--------|
| LCEL chain | Horizon crew report classifier (same prompt/parser pattern as exercise 01) |
| `GET /health` | Returns `{"status": "ok"}` |
| `add_routes` | Mounts the chain at `/classify` |

## Step-by-step

### 1. Build the chain

Copy the `ChatPromptTemplate`, `ChatOpenAI`, and `JsonOutputParser` pattern from exercise 01 (Horizon system message).

```python
chain = prompt | ChatOpenAI(model="gpt-4o-mini", temperature=0) | JsonOutputParser()
```

### 2. Implement `create_app()`

```python
from fastapi import FastAPI
from langserve import add_routes

def create_app() -> FastAPI:
    app = FastAPI(title="Horizon Report API")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    add_routes(app, chain, path="/classify")
    return app
```

### 3. Run the server

```bash
cd module-10-langchain/exercises/04-langserve-api
uvicorn start:create_app --factory --reload
```

Open:

- API docs: http://127.0.0.1:8000/docs
- Playground: http://127.0.0.1:8000/classify/playground/

### 4. Call the API

```bash
curl -s -X POST http://127.0.0.1:8000/classify/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": {"report": "Main drive output at 91% during station power draw."}}'
```

Response shape: `{"output": {"category": "...", "summary": "...", "priority": "..."}}`.

## Tests

```bash
pytest test_start.py -v
```

Tests without an API key:

- `GET /health` returns 200
- OpenAPI lists `/classify/invoke`

Integration test (requires `OPENAI_API_KEY`):

```bash
pytest test_start.py -v -m integration
```

## Stretch goals

- Add a `POST /classify/batch` call from httpx with multiple reports
- Try `/classify/stream` and print tokens as they arrive
- Add CORS middleware for a future frontend

## Reference

- [LangServe](https://github.com/langchain-ai/langserve)
- Module demo: `module-10-langchain/demo/04_langserve.py`
