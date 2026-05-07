# Exercise 03 — Mission API

**Mission briefing:** HQ wants a REST API so bridge officers can query, create, and update mission records from any terminal on the ship. Build a FastAPI app that serves mission data, and prove it works with httpx tests.

## Objectives

1. Implement `create_app()` — returns a FastAPI application with missions loaded from JSON.
2. `GET /missions` — returns all missions; supports optional `?status=active` filter.
3. `GET /missions/{mission_id}` — returns a single mission or 404.
4. `POST /missions` — accepts a JSON body and adds a new mission. Returns 201.
5. `PATCH /missions/{mission_id}` — partial update of an existing mission.

## Run the tests

```bash
pytest module-01-python-fundamentals/exercises/03-mission-api/test_start.py -v
```

## Hints

- Store missions in a plain `list[dict]` on `app.state.missions`.
- Use `httpx.ASGITransport` + `httpx.AsyncClient` to test without starting a real server.
- For the PATCH endpoint, merge the request body into the existing mission dict.
