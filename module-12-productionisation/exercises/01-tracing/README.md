# Exercise 01 — Structured Tracing

## Recap

A crew member says the Pathfinder gave them a bad answer this morning. Which request was it? Which logs did it retrieve, which model answered, and where did the four seconds go?

A **trace ID** is one string attached to a request and carried through every function it touches. A **span** is one unit of work inside that trace — a retrieval, an LLM call, a guardrail check — with a name, a duration, and whatever metadata is worth keeping. Spans opened inside other spans become their children, so a finished trace is a tree:

```
trace 4f2a9c1e8b3d7a60
  handle_request  142.0ms  [ok]
    retrieve_logs  38.0ms  [ok]
      embed_query  12.0ms  [ok]
      search_index  24.0ms  [ok]
    llm_call  95.0ms  [ok]
    guardrail_check  9.0ms  [ok]
```

Each span is also emitted as a single line of JSON. That is the part that matters in production: Datadog, Grafana, and CloudWatch index the fields, so `trace_id` and `duration_ms` become things you filter and aggregate on rather than text you parse back out of a log message.

This is the real `TraceContext` the capstones in this module (`04-recipe-finder` through `07-personal-assistant`) import.

### Two details worth knowing before you start

**The clock is injectable.** `TraceContext` takes a `clock` argument defaulting to `time.monotonic`, not `time.time`. A monotonic clock only moves forward, so an NTP adjustment in the middle of a request cannot produce a negative duration. It also means the tests can pass a fake clock and assert exact durations instead of sleeping.

**`self.spans` is in completion order, not start order.** An inner span closes before the outer span that contains it, so `handle_request` is the *last* entry in the list even though it started first. That is why each span records a `seq` number — `summary()` sorts on it to print the tree in the order a reader expects.

## What you build

Three methods on `TraceContext` in **`start.py`**. The `handle_query` pipeline below them is already written.

| Method | What it does |
|---|---|
| `start_span(name, metadata)` | Open a span under whatever span is currently open; return its ID |
| `end_span(span_id, metadata, status)` | Close it, record `duration_ms`, merge metadata, emit one JSON record |
| `summary()` | Render the completed spans as an indented tree |

A completed span looks like:

```python
{
    "span_id": "a1b2c3d4e5f6",
    "trace_id": "4f2a9c1e8b3d7a60",
    "parent_id": "9f8e7d6c5b4a",   # None for the root
    "name": "llm_call",
    "seq": 3,
    "start": 1041.22,
    "duration_ms": 95.0,
    "status": "ok",
    "metadata": {"model": "gpt-6-luna", "tokens": 210},
}
```

The record handed to `emit` is **flat** — metadata spread at the top level, no `start`, no `seq`:

```python
{
    "trace_id": "4f2a9c1e8b3d7a60",
    "span_id": "a1b2c3d4e5f6",
    "parent_id": "9f8e7d6c5b4a",
    "name": "llm_call",
    "duration_ms": 95.0,
    "status": "ok",
    "model": "gpt-6-luna",
    "tokens": 210,
}
```

Flat matters because log platforms index top-level fields. A nested `metadata` object is one blob you cannot filter on.

## Step-by-step

### 1. `start_span`

Generate a span ID with `uuid.uuid4().hex[:12]`. The parent is the innermost span still open — the last entry in `self._stack`, or `None` if the stack is empty. Build the dict, store it in `self._open`, push the ID onto `self._stack`, increment `self._seq`, and return the ID.

Copy the metadata (`dict(metadata or {})`) rather than storing the caller's dict. `end_span` mutates it, and you do not want that reaching back into the caller's object.

### 2. `end_span`

Pop the span out of `self._open` and remove its ID from `self._stack`. Compute `duration_ms` as `(self._clock() - span["start"]) * 1000`, rounded to one decimal place. Set `status`, `update` the metadata rather than replacing it, append to `self.spans`, then call `self._emit` with the flat record above. Return the span.

### 3. `summary`

Start with `f"trace {self.trace_id}"`. Index the spans by `span_id` so you can walk `parent_id` upwards to count a span's depth. Then for each span sorted by `seq`, append:

```python
f"{'  ' * (depth + 1)}{span['name']}  {span['duration_ms']}ms  [{span['status']}]"
```

The `+ 1` keeps everything indented one level under the `trace ...` header.

## Try it

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-12-productionisation/exercises/01-tracing
python start.py

# Option B - uv (no activation needed):
cd module-12-productionisation/exercises/01-tracing
uv run python start.py
```

Traces one simulated request — no API key. You should see six JSON lines go past, then the tree.

## Running Tests

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pytest module-12-productionisation/exercises/01-tracing/test_start.py -v

# Option B - uv (no activation needed):
uv run --extra dev pytest module-12-productionisation/exercises/01-tracing/test_start.py -v
```

## Stretch Goals

- Make `start_span` a context manager so `with trace.span("llm_call"):` closes the span on the way out, including when the body raises. Set `status="error"` in that case.
- Add a `total_ms` to `summary()` and flag any span taking more than half the trace.
- Accept an inbound `X-Trace-Id` header in a FastAPI dependency so a trace continues across services instead of restarting at your edge.
- Emit the spans as [OpenTelemetry](https://opentelemetry.io/docs/concepts/signals/traces/) OTLP instead of JSON lines, and view the tree in Jaeger.
