export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 0 — Python Fundamentals',
      subtitle: 'Core Python for AI development',
      icon: 'code',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'What this module covers',
      points: [
        'This module covers the Python patterns used throughout the course.',
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
      title: 'Data structures',
      icon: 'database',
      points: [
        '**Lists** — ordered, mutable, iterable. User records, event logs.',
        '**Dicts** — O(1) key-value lookup. Lookup tables, configuration.',
        '**Sets** — unique elements, fast membership, set algebra. Tags, categories.',
        '**Tuples** — immutable sequences. Fixed records, function returns.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'List comprehensions',
      code: `users = load_json("users.json")

# Filter + transform in one expression
active_engineers = [
    u["name"]
    for u in users
    if u["role"] == "engineer"
    and u["active_project"] is not None
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
users_by_id = {u["id"]: u for u in users}
admin = users_by_id["USR-003"]

# Count by role
counts: dict[str, int] = {}
for u in users:
    role = u["role"]
    counts[role] = counts.get(role, 0) + 1`,
      highlights: [
        'Dict comprehensions for instant lookups',
        '.get(key, default) avoids KeyError',
      ],
    },
  },
  // ---- Demo: Data structures ----
  {
    type: 'title',
    content: {
      title: 'Demo — Data structures',
      subtitle: 'Switch to terminal: python demo/01_data_structures.py',
      icon: 'terminal',
    },
  },

  // ---- Section: Modules, CLI + logging ----
  {
    type: 'title',
    content: {
      title: 'Modules, CLI + logging',
      subtitle: 'Organising code for maintainable projects',
      icon: 'box',
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
    description="User management CLI"
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
        '`logger.info("Loaded %d records", count)` — lazy formatting.',
        'Production: structured logs (JSON), not print statements.',
      ],
    },
  },
  // ---- Demo: Modules + CLI ----
  {
    type: 'title',
    content: {
      title: 'Demo — Modules + CLI',
      subtitle: 'Switch to terminal: python demo/02_modules_cli.py',
      icon: 'terminal',
    },
  },

  // ---- Section: Dataclasses + Protocol ----
  {
    type: 'title',
    content: {
      title: 'Dataclasses + Protocol',
      subtitle: 'Type-safe domain modelling without inheritance',
      icon: 'file-text',
    },
  },

  {
    type: 'standard',
    content: {
      title: 'Dataclasses and protocols',
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
class Employee:
    id: str
    name: str
    role: str
    access_level: int = 1
    skills: list[str] = field(default_factory=list)
    active_project: str | None = None

    @property
    def is_available(self) -> bool:
        return self.active_project is None`,
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

# Order and Invoice both qualify —
# no shared base class needed`,
      highlights: [
        'Structural subtyping: if it has .briefing(), it qualifies',
        'Keeps agent code loosely coupled and testable',
      ],
    },
  },
  // ---- Demo: Dataclasses + Protocols ----
  {
    type: 'title',
    content: {
      title: 'Demo — Dataclasses + Protocols',
      subtitle: 'Switch to terminal: python demo/03_dataclasses_protocols.py',
      icon: 'terminal',
    },
  },

  // ---- Section: Async essentials ----
  {
    type: 'title',
    content: {
      title: 'Async essentials',
      subtitle: 'Concurrent I/O for agent workloads',
      icon: 'zap',
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
    for event in events:
        await queue.put(event)
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
  // ---- Demo: Async essentials ----
  {
    type: 'title',
    content: {
      title: 'Demo — Async essentials',
      subtitle: 'Switch to terminal: python demo/04_async_essentials.py',
      icon: 'terminal',
    },
  },

  // ---- Section: HTTP basics ----
  {
    type: 'title',
    content: {
      title: 'HTTP basics',
      subtitle: 'APIs and testing with FastAPI + httpx',
      icon: 'globe',
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

@app.get("/projects")
async def list_projects(status: str | None = None):
    results = PROJECTS
    if status:
        results = [p for p in results if p["status"] == status]
    return {"count": len(results), "projects": results}`,
      highlights: [
        'Type hints become query parameter validation',
        'Return dicts/lists — FastAPI serializes to JSON',
      ],
    },
  },
  // ---- Demo: HTTP + FastAPI ----
  {
    type: 'title',
    content: {
      title: 'Demo — HTTP + FastAPI',
      subtitle: 'Switch to terminal: python demo/05_http_basics.py',
      icon: 'terminal',
    },
  },

  // ---- Section: Wrap-up ----
  {
    type: 'title',
    content: {
      title: 'Putting it all together',
      subtitle: 'Field rules and exercises',
      icon: 'check-square',
    },
  },

  {
    type: 'rules',
    content: {
      title: 'Field rules — Module 0',
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
      title: 'Exercises',
      points: [
        '01 — Data processing: dataclasses, filtering, formatting',
        '02 — Async pipeline: queues, timeouts, producer/consumer',
        '03 — REST API: FastAPI CRUD with httpx tests',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Module 0 — Complete',
      subtitle: 'Next: working with the LLM',
      icon: 'check-circle',
    },
  },
];
