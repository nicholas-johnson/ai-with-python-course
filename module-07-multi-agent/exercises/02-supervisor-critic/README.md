# Exercise 02 — Supervisor-Critic Pattern

Implement a supervisor agent that coordinates a researcher (gathers facts) and a critic (validates assumptions), then synthesises a final output.

## Objectives

1. Define messages or steps between supervisor, researcher, and critic.
2. Ensure the critic sees the researcher output before final synthesis.
3. Handle failure (e.g. researcher timeout) gracefully in the workflow.

## Run the tests

```bash
pytest module-07-multi-agent/exercises/02-supervisor-critic/test_start.py -v
```
