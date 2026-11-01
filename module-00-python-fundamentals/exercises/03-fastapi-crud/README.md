# Exercise 03 — FastAPI CRUD

Build a FastAPI application with full CRUD endpoints (list, get, create, update) and test it with httpx.

## Objectives

1. Implement `create_app()` — returns a FastAPI application with missions loaded from JSON.
2. `GET /missions` — returns all missions; supports optional `?status=active` filter.
3. `GET /missions/{mission_id}` — returns a single mission or 404.
4. `POST /missions` — accepts a JSON body and adds a new mission. Returns 201.
5. `PATCH /missions/{mission_id}` — partial update of an existing mission.

## Run the server

Once `create_app()` is implemented, start the API and open the interactive docs at http://127.0.0.1:8000/docs:

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-00-python-fundamentals/exercises/03-fastapi-crud
uvicorn start:app --reload --port 8000

# Option B - uv (no activation needed):
cd module-00-python-fundamentals/exercises/03-fastapi-crud
uv run uvicorn start:app --reload --port 8000
```

## Run the tests

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pytest module-00-python-fundamentals/exercises/03-fastapi-crud/test_start.py -v

# Option B - uv (no activation needed):
uv run --extra dev pytest module-00-python-fundamentals/exercises/03-fastapi-crud/test_start.py -v
```

## Hints

- Store missions in a plain `list[dict]` on `app.state.missions`.
- Use `httpx.ASGITransport` + `httpx.AsyncClient` to test without starting a real server.
- For the PATCH endpoint, merge the request body into the existing mission dict.
