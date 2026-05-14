# Exercise 04 — Deploy Container

**Mission briefing:** The Pathfinder's AI systems need to ship in a container so they run identically on every platform. Build a minimal FastAPI health-check app, validate its Dockerfile, and configure environment-based settings.

## Objectives

1. Write a `create_app` function that returns a FastAPI app with a `GET /health` endpoint.
2. Implement `load_config` that reads settings from environment variables with sensible defaults.
3. Write a `validate_dockerfile` function that checks a Dockerfile string for required instructions (FROM, EXPOSE, HEALTHCHECK, CMD).

## Run the tests

```bash
pytest module-11-production/exercises/04-deploy-container/test_start.py -v
```
