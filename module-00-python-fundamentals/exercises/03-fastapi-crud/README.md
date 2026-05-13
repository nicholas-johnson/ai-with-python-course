# Exercise 03 — FastAPI CRUD

Build a FastAPI application with full CRUD endpoints (list, get, create, update) and test it with httpx.

## Objectives

1. Implement `create_app()` — returns a FastAPI application with missions loaded from JSON.
2. `GET /missions` — returns all missions; supports optional `?status=active` filter.
3. `GET /missions/{mission_id}` — returns a single mission or 404.
4. `POST /missions` — accepts a JSON body and adds a new mission. Returns 201.
5. `PATCH /missions/{mission_id}` — partial update of an existing mission.

## Run the tests

```bash
pytest module-00-python-fundamentals/exercises/03-fastapi-crud/test_start.py -v
```

## Hints

- Store missions in a plain `list[dict]` on `app.state.missions`.
- Use `httpx.ASGITransport` + `httpx.AsyncClient` to test without starting a real server.
- For the PATCH endpoint, merge the request body into the existing mission dict.
