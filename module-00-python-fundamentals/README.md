# Module 0 — Python Fundamentals

> The DSS Pathfinder runs Python from bridge to engine room. Before we build a single agent, every subsystem — crew manifests, sensor telemetry, mission briefings — needs a solid foundation. This module is your systems check: data structures for wrangling ship records, modules and CLI tools for automation, dataclasses and Protocols for clean architecture, async for concurrent I/O, and a FastAPI service so the rest of the fleet can query mission data over HTTP.

## Learning goals

- Work fluently with Python **data structures**: lists, dicts, sets, tuples.
- Organise code with **modules/packages**, CLI args (`argparse`), and **logging**.
- Model domain objects with **dataclasses** and define contracts with **Protocol**.
- Write **async** code: `asyncio` tasks, queues, timeouts, cancellation.
- Build and test a basic **HTTP API** with FastAPI and httpx.

---

## Data structures — the cargo hold

Every piece of data on the Pathfinder — crew records, sensor readings, mission objectives — lives in one of four core structures. Pick the right one and your code stays fast and readable.

**Lists** are ordered, mutable sequences. They are the default when you need to iterate, filter, or accumulate. Crew rosters, sensor reading buffers, and log entries are all natural lists.

```python
crew = json.loads(Path("data/crew.json").read_text())

# List comprehension: filter + transform in one expression
active_scientists = [
    m["name"]
    for m in crew
    if m["department"] == "science"
    and m["activeMission"] is not None
]
```

**Dicts** give you O(1) key-value lookup. Build one whenever you need to find a record by ID without scanning the whole list.

```python
crew_by_id = {m["id"]: m for m in crew}
engineer = crew_by_id["CRW-003"]   # Chief Engineer Mira Chen, instantly

# Count by department with .get(key, default) to avoid KeyError
counts: dict[str, int] = {}
for m in crew:
    dept = m["department"]
    counts[dept] = counts.get(dept, 0) + 1
```

**Sets** store unique elements and support fast membership tests and set algebra. Useful when you care about "which skills exist" rather than "how many of each."

```python
science_specs = {s for m in crew if m["department"] == "science" for s in m["specializations"]}
eng_specs = {s for m in crew if m["department"] == "engineering" for s in m["specializations"]}

shared = science_specs & eng_specs       # intersection
science_only = science_specs - eng_specs  # difference
```

**Tuples** are immutable sequences — good for fixed records and function return values. Because they cannot be changed after creation, they are safe to use as dict keys.

```python
mission_summaries = [
    (m["id"], m["name"], m["status"], m["riskLevel"])
    for m in missions
]
for mid, name, status, risk in mission_summaries:
    print(f"  {mid} {name:<30} {status:<12} risk: {'*' * risk}")
```

**When to use what:** lists for ordered collections you will filter or grow; dicts for fast lookup by key; sets for membership and algebra; tuples for fixed records.

---

## Modules, CLI args, and logging

Real ship tools are not Jupyter notebooks — they are command-line programs that log what they do. Python gives you `argparse` for CLI arguments and `logging` for structured output.

**Modules and `__main__`** — every `.py` file is a module. The `if __name__ == "__main__":` guard lets a file work both as an importable library and as a standalone script.

```python
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pathfinder.crew")

parser = argparse.ArgumentParser(description="Pathfinder crew query tool")
parser.add_argument("--department", "-d")
parser.add_argument("--min-clearance", "-c", type=int, default=0)
args = parser.parse_args()
```

**Logging beats `print()`** in every way that matters for production. Levels (DEBUG → INFO → WARNING → ERROR → CRITICAL) let you control verbosity without deleting code. Lazy formatting (`logger.info("Loaded %d crew", count)`) avoids string interpolation when the message would be filtered out anyway. In production, switch to JSON-structured logs so your aggregator can parse them.

---

## Dataclasses — structured ship records

Plain dicts are fine for throwaway data. Anything that lives longer than a few lines deserves a `@dataclass`. You get `__init__`, `__repr__`, and `__eq__` for free, plus type hints that document the shape.

```python
from dataclasses import dataclass, field

@dataclass
class CrewMember:
    id: str
    name: str
    role: str
    department: str
    clearance_level: int = 1
    specializations: list[str] = field(default_factory=list)
    active_mission: str | None = None

    @property
    def is_available(self) -> bool:
        return self.active_mission is None
```

Key details:
- `field(default_factory=list)` prevents the mutable-default trap (all instances sharing one list).
- `str | None` is Python 3.10+ union syntax — cleaner than `Optional[str]`.
- Properties like `is_available` give you derived state without extra storage.
- Prefer returning new instances over mutating existing ones (immutable style) — this makes debugging agent state much easier later.

---

## Protocol — contracts without inheritance

The Pathfinder's agent components — tools, memory backends, formatters — need to agree on interfaces without forcing a shared base class. `typing.Protocol` defines a structural (duck-typed) contract: any object with matching methods satisfies it.

```python
from typing import Protocol

class Briefable(Protocol):
    def briefing(self) -> str: ...

def print_briefings(items: list[Briefable]):
    for item in items:
        print(item.briefing())
```

`Mission` and `ShipSystem` can both implement `briefing()` independently — no inheritance chain, no import dependency. This keeps agent code loosely coupled and testable. You will use this pattern heavily when building pluggable session backends in Module 1 and tool registries in Module 2.

---

## Async essentials — why it matters for agents

AI agents spend most of their time waiting — on LLM API responses, tool server calls, database queries. Synchronous code blocks the entire thread on each wait. `async`/`await` lets one thread handle many concurrent waits, which is exactly what an agent orchestrator needs.

**Key primitives:**

```python
import asyncio

# Run multiple scans concurrently
results = await asyncio.gather(
    scan_sector("Alpha-7", 0.5),
    scan_sector("Beta-12", 0.3),
    scan_sector("Gamma-3", 0.8),
)
```

**Producer/consumer with Queue** — the pattern you will use for streaming sensor data:

```python
async def producer(queue: asyncio.Queue):
    for reading in sensor_data:
        await queue.put(reading)
    await queue.put(None)  # sentinel signals "no more data"

async def consumer(queue: asyncio.Queue):
    while (item := await queue.get()) is not None:
        process(item)

queue = asyncio.Queue(maxsize=5)  # maxsize creates backpressure
await asyncio.gather(producer(queue), consumer(queue))
```

**Timeouts** wrap any coroutine with a deadline. **Cancellation** lets you shut down cleanly when the user walks away.

```python
# Timeout: abort if the scan takes too long
try:
    result = await asyncio.wait_for(long_scan(), timeout=2.0)
except asyncio.TimeoutError:
    print("Scan timed out")

# Cancellation: clean shutdown
task = asyncio.create_task(monitor())
await asyncio.sleep(5)
task.cancel()  # CancelledError propagates for cleanup
```

---

## HTTP basics — FastAPI + httpx

The Pathfinder exposes mission data over HTTP so other ships and stations can query it. **FastAPI** is modern, async-native, and generates OpenAPI docs automatically. **httpx** is the async-capable HTTP client you use to test it.

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/missions")
async def list_missions(status: str | None = None):
    results = MISSIONS
    if status:
        results = [m for m in results if m["status"] == status]
    return {"count": len(results), "missions": results}
```

Type hints on parameters become automatic query parameter validation. Return dicts or lists and FastAPI serializes to JSON. Test without a real server using `httpx.ASGITransport`:

```python
transport = httpx.ASGITransport(app=app)
async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
    resp = await client.get("/missions", params={"status": "active"})
    assert resp.status_code == 200
```

---

## Field rules

- **Use dataclasses for domain objects.** Dicts are fine for JSON; dataclasses are better for code.
- **Async for I/O, sync for computation.** Agent loops are mostly I/O — async is the default.
- **Log, do not print.** `logging.info` > `print()` in anything beyond a throwaway demo.

---

## Demos

```bash
python module-00-python-fundamentals/demo/01_data_structures.py
python module-00-python-fundamentals/demo/02_modules_cli.py --department science
python module-00-python-fundamentals/demo/03_dataclasses_protocols.py
python module-00-python-fundamentals/demo/04_async_essentials.py
python module-00-python-fundamentals/demo/05_http_basics.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-dataclass-filtering`](exercises/01-dataclass-filtering/) | Parse, filter, and transform crew JSON with dataclasses and CLI args. |
| [`exercises/02-async-queue-processing`](exercises/02-async-queue-processing/) | Async queue processing of ship sensor data with timeouts. |
| [`exercises/03-fastapi-crud`](exercises/03-fastapi-crud/) | FastAPI CRUD for missions with httpx test client. |

Run tests for this module:

```bash
pytest module-00-python-fundamentals/
```

## Slides

From repo root: `pnpm slides:00`, or `cd module-00-python-fundamentals/slides && pnpm dev`.

## Reference

- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [asyncio](https://docs.python.org/3/library/asyncio.html)
- [FastAPI](https://fastapi.tiangolo.com/)
- [httpx](https://www.python-httpx.org/)
- [typing.Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
