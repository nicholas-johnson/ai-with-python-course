# Module 11 — Production & Deployment

**Launch is not the finish line.** Agentic systems on the Pathfinder must be observable, resilient, and affordable to run — and they need to ship reliably across environments. This module covers the full journey from code to production: structured tracing, reliability patterns, cost controls, environment config, secrets, containerisation, and CI/CD basics.

## Learning goals

- Add **tracing and structured logging** so every tool call is attributable and debuggable.
- Implement **reliability** patterns: retries, timeouts, **circuit breakers**, and fallbacks.
- Apply **cost controls**: caching, batching, model selection, and token budgets.
- Ship with confidence: **environment config**, secrets management, **containers**, and CI/CD basics.

## Instructor notes

- **Structured tracing** (`demo/01_structured_tracing.py`): trace IDs, spans, correlating logs with tool calls.
- **Circuit breaker** (`demo/02_circuit_breaker.py`): protecting the ship when external services fail.
- **Deployment pipeline** (`demo/03_deployment_pipeline.py`): environments, secrets, containers, and rollout strategies.

## Demos

```bash
python module-11-production/demo/01_structured_tracing.py
python module-11-production/demo/02_circuit_breaker.py
python module-11-production/demo/03_deployment_pipeline.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-trace-middleware`](exercises/01-trace-middleware/) | Add trace IDs and timing to every tool call in a small agent loop. |
| [`exercises/02-batch-pipeline`](exercises/02-batch-pipeline/) | **Batch** LLM requests with **retry** and **fallback** model. |
| [`exercises/03-cost-tracker`](exercises/03-cost-tracker/) | Track and enforce per-session token or cost budgets. |
| [`exercises/04-deploy-container`](exercises/04-deploy-container/) | Build a **health-check** app, load **env config**, and validate a **Dockerfile**. |

Run tests for this module:

```bash
pytest module-11-production/
```

## Slides

From repo root: `pnpm slides:11`, or `cd module-11-production/slides && pnpm dev`.

## Reference

- [OpenTelemetry](https://opentelemetry.io/docs/)
- [Prometheus metrics best practices](https://prometheus.io/docs/practices/naming/)
- [The Twelve-Factor App — Config](https://12factor.net/config)
- [Docker — Python guide](https://docs.docker.com/language/python/)
- [Google SRE — Handling overload](https://sre.google/sre-book/handling-overload/)
