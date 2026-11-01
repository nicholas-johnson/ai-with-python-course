# Exercise 02 — Reliability

## Recap

The Pathfinder's agent depends on an API it does not control. That API will return a 500, rate-limit you, or go down for maintenance, and none of that is preventable from your side. What you decide is what the service does next.

Three layers, each handling a failure the one before it cannot:

| Layer | Handles | Gets it wrong by |
|---|---|---|
| **Retry with backoff** | A blip — the next call would probably work | Retrying a 401 forever, or retrying so fast you make the outage worse |
| **Circuit breaker** | A dependency that is actually down | Hammering a dead service until every connection is tied up waiting |
| **Fallback chain** | Everything above having failed | Returning a 500 when a cheaper model would have answered |

### Backoff, and why jitter

Each retry waits longer than the last: `base_delay * 2 ** attempt`. With `base_delay=1.0` that is 1s, 2s, 4s — long enough for a transient failure to clear, short enough that the crew is not waiting half a minute.

The **jitter** term is what stops the retries from clumping. Every client that failed during the same outage starts its backoff at the same moment, so without jitter they all come back at second 1, then all at second 3, then all at second 7 — the same spike that caused the failure, arriving on a schedule. A random fraction of `base_delay` added to each delay spreads them out.

### Not everything should be retried

A 500 or a 429 means "try again". A 400 or a 401 means "this request is wrong, and it will still be wrong in four seconds". `start.py` gives you `TransientError` and `PermanentError` to tell them apart, which is the distinction a real client makes by inspecting the status code.

### The breaker's three states

```
                  failures >= threshold
    closed  ─────────────────────────────►  open
      ▲                                      │
      │                                      │ cooldown elapsed
      │ success                              ▼
      └──────────────────────────────  half-open
                                             │ failure
                                             └──► open (cooldown restarts)
```

**Closed** is normal. **Open** means calls are rejected without being attempted, which is the whole point — a dead dependency stops occupying connections that healthy requests need. **Half-open** is the cooldown having elapsed: let one call through and see. If it works, close. If it does not, reopen and wait again.

Both the clock and `sleep` are injected here for the same reason as the trace clock in exercise 01: the tests drive time by hand rather than waiting for it.

## What you build

Three pieces in **`start.py`**. `CircuitBreaker.call` and the simulated services are written for you.

| Piece | What it does |
|---|---|
| `retry_with_backoff(fn, ...)` | Retry transient failures with a doubling, jittered delay |
| `CircuitBreaker.allow_request/record_success/record_failure` | The state machine above |
| `chat_with_fallback(chain)` | Walk the rungs, return the first answer, never raise |

`chat_with_fallback` returns:

```python
{
    "answer": "Hull integrity 98%, shields nominal",
    "step": "gpt-6-luna",                                  # which rung produced it
    "attempts": [{"step": "gpt-6-sol", "error": "503"}],   # the rungs that failed
}
```

When every rung fails it returns `FALLBACK_MESSAGE` with `"step": "unavailable"`. It does not raise — that is the contract. The crew gets a sentence rather than a stack trace.

## Step-by-step

### 1. `retry_with_backoff`

Loop over `attempt in range(max_retries + 1)` — `max_retries=3` means four calls in total, one attempt plus three retries.

- `try: return fn()`
- `except PermanentError: raise` — immediately, with no delay.
- `except TransientError:` — if `attempt == max_retries` this was the last chance, so re-raise. Otherwise `sleep(base_delay * (2 ** attempt) + jitter() * base_delay)` and go round again.

Call `sleep` and `jitter` through the injected parameters, not `time.sleep` and `random.random` directly, or the tests will take real seconds and assert random numbers.

### 2. `CircuitBreaker`

`allow_request` reads the state and may advance it:

- `closed` → `True`.
- `open` → if `self._clock() - self.opened_at >= self.cooldown_seconds`, set `state = "half-open"` and return `True`. Otherwise `False`.
- `half-open` → `True`.

`record_success` resets `failures` to 0 and the state to `closed`.

`record_failure` increments `failures`, then opens the circuit if `failures >= failure_threshold` **or** the state is already `half-open` — a failed test request means the dependency is still down, so it reopens on the first failure rather than waiting for three more. Stamp `opened_at = self._clock()` when you open, which is what restarts the cooldown.

### 3. `chat_with_fallback`

Walk the chain, returning on the first rung that does not raise. Catch bare `Exception`, not just `TransientError` — this is the last line of defence, and an unexpected `ValueError` from a cache lookup should still fall through to the next rung rather than escaping to the user.

## Try it

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-12-productionisation/exercises/02-reliability
python start.py

# Option B - uv (no activation needed):
cd module-12-productionisation/exercises/02-reliability
uv run python start.py
```

No API key, and no real waiting — the demo injects a fake clock and records the delays instead of sleeping through them. The breaker section prints the state transition on each call:

```
   t=   4s  closed    -> closed     failed — 503 from telemetry (call 1)
   t=  12s  closed    -> open       failed — 503 from telemetry (call 3)
   t=  16s  open      -> open       rejected — Circuit open; not calling (failures=3)
   t=  24s  open      -> open       failed — 503 from telemetry (call 4)
```

## Running Tests

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pytest module-12-productionisation/exercises/02-reliability/test_start.py -v

# Option B - uv (no activation needed):
uv run --extra dev pytest module-12-productionisation/exercises/02-reliability/test_start.py -v
```

## Stretch Goals

- Port `retry_with_backoff` to `async def` with `asyncio.sleep`. Same shape, one `await` — that is the version a FastAPI handler wants.
- Cap the delay at a `max_delay` so attempt 8 does not wait four minutes.
- Add a **retry budget**: refuse to retry at all if more than 10% of calls in the last minute were retries. Backoff limits one client; a budget limits the fleet.
- Give the breaker a half-open limit of *n* concurrent test requests rather than letting every caller through at once.
- Wire the fallback chain to the `TraceContext` from [exercise 01](../01-tracing/), opening a span per rung so a degraded answer is visible in the trace.
