# Exercise 02 — Research team

**Mission briefing:** A supervisor agent coordinates a researcher (gathers facts from tools/data) and a critic (checks assumptions). Produce a merged mission briefing.

## Objectives

1. Define messages or steps between supervisor, researcher, and critic.
2. Ensure the critic sees the researcher output before final synthesis.
3. Handle failure (e.g. researcher timeout) gracefully in the workflow.

## Run the tests

```bash
pytest module-09-multi-agent/exercises/02-research-team/test_start.py -v
```
