# Module 1 — Python Fundamentals: Systems Programming for the DSS Pathfinder

**All hands to stations.** The Pathfinder's AI subsystems run Python end to end — from parsing crew manifests and routing sensor telemetry to serving mission data over HTTP. Before we wire up a single agent, we need a solid Python workflow: **data structures**, **modules**, **async**, and a **web API**.

## Learning goals

- Work fluently with Python **data structures**: lists, dicts, sets, tuples.
- Organise code with **modules/packages**, CLI args (`argparse`), and **logging**.
- Model domain objects with **dataclasses** and define contracts with **Protocol**.
- Write **async** code: `asyncio` tasks, queues, timeouts, cancellation.
- Build and test a basic **HTTP API** with FastAPI and httpx.

## Instructor notes

- **Data structures** (demo `01_data_structures.py`): list comprehensions, dict operations, set algebra, tuple unpacking — all using crew and mission data.
- **Modules and CLI** (demo `02_modules_cli.py`): `__name__ == "__main__"`, package imports, `argparse`, structured logging with the `logging` module.
- **Dataclasses and Protocols** (demo `03_dataclasses_protocols.py`): OOP vs functional style for agents — when to use `@dataclass` vs plain dicts, `Protocol` for duck-typing contracts.
- **Async essentials** (demo `04_async_essentials.py`): event loop, `async`/`await`, `asyncio.create_task`, `asyncio.Queue`, `asyncio.wait_for` (timeouts), `Task.cancel`.
- **HTTP basics** (demo `05_http_basics.py`): FastAPI app with path/query params, httpx as the async-capable HTTP client.

## Demos

From the repo root:

```bash
python module-01-python-fundamentals/demo/01_data_structures.py
python module-01-python-fundamentals/demo/02_modules_cli.py --department science
python module-01-python-fundamentals/demo/03_dataclasses_protocols.py
python module-01-python-fundamentals/demo/04_async_essentials.py
python module-01-python-fundamentals/demo/05_http_basics.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-crew-manifest`](exercises/01-crew-manifest/) | Parse, filter, and transform crew JSON with dataclasses and CLI args. |
| [`exercises/02-async-sensor-relay`](exercises/02-async-sensor-relay/) | Async queue processing of ship sensor data with timeouts. |
| [`exercises/03-mission-api`](exercises/03-mission-api/) | FastAPI CRUD for missions with httpx test client. |

Run tests for this module:

```bash
pytest module-01-python-fundamentals/
```

## Slides

Teaching deck (Vite + [`slide-deck`](../slide-deck/)): from repo root run `pnpm slides:01`, or `cd module-01-python-fundamentals/slides && pnpm dev`.

## Reference

- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [asyncio](https://docs.python.org/3/library/asyncio.html)
- [FastAPI](https://fastapi.tiangolo.com/)
- [httpx](https://www.python-httpx.org/)
- [typing.Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
