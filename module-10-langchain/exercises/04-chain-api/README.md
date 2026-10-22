# Exercise 4: Chain API

> **Scenario:** Hands-on work uses the **CSS Horizon** cargo survey vessel. Module demo 04 uses the **DSS Pathfinder** — same pattern, different vessel name in the prompt.

## Recap

You built an LCEL classifier in exercise 01. Every LCEL chain is a **Runnable**, so it already has `invoke`, `batch`, and `stream` — plus async versions `ainvoke`, `abatch`, and `astream`. Serving a chain over HTTP is just a thin FastAPI layer on top of those methods:

```python
@app.post("/classify/invoke")
async def classify_invoke(req: InvokeRequest):
    return InvokeResponse(output=await chain.ainvoke(req.input.model_dump()))
```

> **Why not LangServe?** Older tutorials use `langserve.add_routes`. LangServe is no longer maintained and is incompatible with current dependencies (it pins `sse-starlette<2`). Writing the routes yourself is a few lines of FastAPI and gives you full control over validation, auth, and response shape. For agent deployments, LangChain now points to LangGraph/LangSmith deployment instead.

## What you build

A FastAPI app in **`start.py`** that:

| Piece | Detail |
|-------|--------|
| LCEL chain | Horizon crew report classifier (same `Classification` structured-output chain as exercise 01) |
| Pydantic models | `ReportInput` / `InvokeRequest` validate the request; `InvokeResponse` types the response |
| `GET /health` | Returns `{"status": "ok"}` |
| `POST /classify/invoke` | Runs the chain and returns `{"output": {...}}` |

## Step-by-step

### 1. Build the chain

Copy the `Classification` model, prompt, and structured-output chain from exercise 01.

```python
model = ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0)
chain = prompt | model.with_structured_output(Classification)
```

### 2. Define request and response models

```python
from pydantic import BaseModel

class ReportInput(BaseModel):
    report: str

class InvokeRequest(BaseModel):
    input: ReportInput

class InvokeResponse(BaseModel):
    output: Classification
```

FastAPI rejects a body without `input.report` with a `422` before your chain ever runs. Because the chain already returns a Pydantic `Classification`, the same model types your response — and shows up in the OpenAPI docs with the allowed `category` and `priority` values.

### 3. Implement `create_app()`

```python
from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(title="Horizon Report API")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/classify/invoke")
    async def classify_invoke(req: InvokeRequest) -> InvokeResponse:
        return InvokeResponse(output=await chain.ainvoke(req.input.model_dump()))

    return app
```

Use `ainvoke` (not `invoke`) inside an `async def` route so the server is not blocked while waiting on the model.

### 4. Run the server

```bash
cd module-10-langchain/exercises/04-chain-api
uvicorn start:create_app --factory --reload
```

Open the API docs at http://127.0.0.1:8000/docs and try the endpoint from the browser.

### 5. Call the API

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
- A body missing `report` returns 422

Integration test (requires `OPENAI_API_KEY`):

```bash
pytest test_start.py -v -m integration
```

## Stretch goals

- Add `POST /classify/batch` that takes `{"inputs": [...]}` and calls `chain.abatch(...)`
- Add `POST /classify/stream` that returns a `StreamingResponse` of NDJSON. Structured output arrives as one complete object, so stream a `prompt | model | JsonOutputParser()` chain instead (with a prompt that asks for JSON) — it yields the partial object as it fills in
- Add CORS middleware for a future frontend

## Reference

- [LangChain Runnable reference](https://reference.langchain.com/python/langchain-core/runnables)
- [FastAPI request bodies](https://fastapi.tiangolo.com/tutorial/body/)
- Module demo: `module-10-langchain/demo/04_serving_chains.py`
