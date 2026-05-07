export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 1 — Python Fundamentals',
      subtitle: 'Ship systems programming for the DSS Pathfinder',
      icon: 'rocket',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'All hands to stations',
      points: [
        'The Pathfinder runs Python from bridge to engine room.',
        'Before we build a single agent, we need a solid foundation.',
        'Data structures, modules, async, and HTTP — the core toolkit.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Work fluently with **lists, dicts, sets, tuples**.',
        'Organise code with **modules**, CLI args, and **logging**.',
        'Model domain objects with **dataclasses** and **Protocol**.',
        'Write **async** code: tasks, queues, timeouts, cancellation.',
        'Build and test a basic **HTTP API** with FastAPI + httpx.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Data structures — the cargo hold',
      icon: 'database',
      points: [
        '**Lists** — ordered, mutable, iterable. Crew roster, sensor readings.',
        '**Dicts** — O(1) key-value lookup. Crew by ID, config maps.',
        '**Sets** — unique elements, fast membership, set algebra. Specializations.',
        '**Tuples** — immutable sequences. Fixed records, function returns.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'List comprehensions',
      code: `crew = load_json("crew.json")

# Filter + transform in one expression
active_scientists = [
    m["name"]
    for m in crew
    if m["department"] == "science"
    and m["activeMission"] is not None
]`,
      highlights: [
        'Comprehensions replace verbose for-loops for filter+map',
        'Readable, efficient, and Pythonic',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Dict operations',
      code: `# Build a lookup table
crew_by_id = {m["id"]: m for m in crew}
engineer = crew_by_id["CRW-003"]

# Count by department
counts: dict[str, int] = {}
for m in crew:
    dept = m["department"]
    counts[dept] = counts.get(dept, 0) + 1`,
      highlights: [
        'Dict comprehensions for instant lookups',
        '.get(key, default) avoids KeyError',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Modules and packages',
      icon: 'box',
      points: [
        '`import json`, `from pathlib import Path` — standard library.',
        '`if __name__ == "__main__":` — script vs import guard.',
        'Packages = directories with `__init__.py` (or implicit namespace).',
        'Keep imports at the top; organise by stdlib → third-party → local.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'CLI with argparse',
      code: `import argparse

parser = argparse.ArgumentParser(
    description="Pathfinder crew query tool"
)
parser.add_argument("--department", "-d")
parser.add_argument("--min-clearance", "-c", type=int, default=0)
args = parser.parse_args()`,
      highlights: [
        'argparse is stdlib — no extra dependencies',
        'Type conversion, defaults, and help text built in',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Logging — better than print()',
      icon: 'clipboard-list',
      points: [
        '`logging.basicConfig(level=logging.INFO)` — one-line setup.',
        'Levels: DEBUG → INFO → WARNING → ERROR → CRITICAL.',
        '`logger.info("Loaded %d crew", count)` — lazy formatting.',
        'Production: structured logs (JSON), not print statements.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Dataclasses — structured ship records',
      icon: 'file-text',
      points: [
        '`@dataclass` generates `__init__`, `__repr__`, `__eq__` for you.',
        'Type hints document the shape; defaults reduce boilerplate.',
        '`field(default_factory=list)` for mutable defaults.',
        'Immutable style: return new instances instead of mutating.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Dataclass example',
      code: `from dataclasses import dataclass, field

@dataclass
class CrewMember:
    id: str
    name: str
    role: str
    clearance_level: int = 1
    specializations: list[str] = field(default_factory=list)
    active_mission: str | None = None

    @property
    def is_available(self) -> bool:
        return self.active_mission is None`,
      highlights: [
        'str | None — Python 3.10+ union syntax',
        'Properties for derived state without extra storage',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Protocol — contracts without inheritance',
      icon: 'shield',
      points: [
        '`typing.Protocol` defines a structural interface.',
        'Any class with matching methods satisfies it — no base class needed.',
        'Perfect for agent components: tools, memory backends, formatters.',
        'Duck typing with type checker support.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Protocol in action',
      code: `from typing import Protocol

class Briefable(Protocol):
    def briefing(self) -> str: ...

def print_briefings(items: list[Briefable]):
    for item in items:
        print(item.briefing())

# Mission and ShipSystem both work —
# no shared base class needed`,
      highlights: [
        'Structural subtyping: if it has .briefing(), it qualifies',
        'Keeps agent code loosely coupled and testable',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Async essentials — why it matters for agents',
      icon: 'zap',
      points: [
        'AI agents wait on network calls — LLM APIs, tool servers, databases.',
        '`async`/`await` lets one thread handle many concurrent waits.',
        'Key primitives: `asyncio.create_task`, `gather`, `Queue`, `wait_for`.',
        '`Task.cancel()` for cleanup when the user walks away.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Async producer / consumer',
      code: `import asyncio

async def producer(queue: asyncio.Queue):
    for reading in sensor_data:
        await queue.put(reading)
    await queue.put(None)  # sentinel

async def consumer(queue: asyncio.Queue):
    while (item := await queue.get()) is not None:
        process(item)

queue = asyncio.Queue(maxsize=5)
await asyncio.gather(producer(queue), consumer(queue))`,
      highlights: [
        'Queue with maxsize creates backpressure',
        'None sentinel signals "no more data"',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Timeouts and cancellation',
      code: `# Timeout: abort if too slow
try:
    result = await asyncio.wait_for(
        long_scan(), timeout=2.0
    )
except asyncio.TimeoutError:
    print("Scan timed out")

# Cancellation: clean shutdown
task = asyncio.create_task(monitor())
await asyncio.sleep(5)
task.cancel()`,
      highlights: [
        'wait_for wraps any coroutine with a deadline',
        'CancelledError propagates for cleanup in try/except',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'HTTP basics — FastAPI + httpx',
      icon: 'globe',
      points: [
        '**FastAPI** — modern, async, auto-generates OpenAPI docs.',
        '**httpx** — async-capable HTTP client (like requests but better).',
        'Path params, query params, JSON bodies — all typed.',
        'Test with `httpx.ASGITransport` — no real server needed.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'FastAPI in 10 lines',
      code: `from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/missions")
async def list_missions(status: str | None = None):
    results = MISSIONS
    if status:
        results = [m for m in results if m["status"] == status]
    return {"count": len(results), "missions": results}`,
      highlights: [
        'Type hints become query parameter validation',
        'Return dicts/lists — FastAPI serializes to JSON',
      ],
    },
  },
  {
    type: 'rules',
    content: {
      title: 'Field rules — Module 1',
      rules: [
        {
          rule: 'Use dataclasses for domain objects',
          example: 'Dicts are fine for JSON; dataclasses are better for code.',
          icon: 'scale',
        },
        {
          rule: 'async for I/O, sync for computation',
          example: 'Agent loops are mostly I/O — async is the default.',
          icon: 'zap',
        },
        {
          rule: 'Log, do not print',
          example: 'logging.info > print() in anything beyond a demo.',
          icon: 'clipboard-list',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises — Pathfinder systems check',
      points: [
        '01 — Crew manifest: dataclasses, filtering, formatting',
        '02 — Async sensor relay: queues, timeouts, producer/consumer',
        '03 — Mission API: FastAPI CRUD with httpx tests',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Stations secured — Module 1',
      subtitle: 'Run the demos, pass the tests, then report to Module 2',
      icon: 'party-popper',
    },
  },
];
