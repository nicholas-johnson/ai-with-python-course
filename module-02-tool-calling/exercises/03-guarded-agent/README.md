# Exercise 03 -- Guarded Agent

> Wrap the tool-calling agent with safety rails -- an allowlist that restricts which tools can be called, a rate limiter that prevents runaway loops, and an audit log that records everything.

## Recap

An unguarded agent will call whatever tools the model asks for, as many times as it wants. In production, that is a problem. The model might hallucinate a tool name, call a destructive tool repeatedly, or get stuck in a loop that burns through your API budget.

**Safety rails** address this with three layers:

**Allowlists** restrict which tools the agent can call. If a tool is not in the permitted set, the call is rejected before it reaches any handler. The agent receives an error message so it can explain the denial to the user or try a different approach.

**Rate limiters** prevent runaway loops. A sliding-window limiter tracks recent timestamps and blocks calls when the count exceeds a threshold:

```python
class RateLimiter:
    def __init__(self, max_calls, window_seconds):
        self.max_calls = max_calls
        self.window = window_seconds
        self._timestamps = []

    def allow(self):
        now = time.time()
        # Prune old timestamps
        self._timestamps = [t for t in self._timestamps if now - t < self.window]
        if len(self._timestamps) >= self.max_calls:
            return False
        self._timestamps.append(now)
        return True
```

**Audit logging** records every tool call -- allowed or blocked -- so you can debug incidents, measure usage, and prove compliance. Each entry records the timestamp, tool name, arguments, whether it was allowed, and the result.

The key design decision: when a tool is blocked, you do **not** crash or silently skip the call. Instead, you send back an error message as the tool result so the model can see it and adapt. This keeps the conversation flowing.

This exercise builds on Exercise 02. The `ToolRegistry`, tool registrations, and ship data are provided from the Exercise 02 solution. You only need to implement `AllowList`, `RateLimiter`, and `GuardedAgent`.

## What you build

- **`AllowList`** -- checks whether a tool name is in the permitted set.
- **`RateLimiter`** -- sliding-window rate limiter.
- **`GuardedAgent`** -- wraps the agent loop with allowlist + rate limit checks and an audit log.

## Step-by-step

### 1. Implement `AllowList.check(name) -> bool`

This is the simplest class. Check whether `name` is in `self._permitted` and return `True` or `False`.

```python
def check(self, name: str) -> bool:
    return name in self._permitted
```

The tests create an allowlist with `{"get_crew_count", "get_ship_status"}` and check that `search_crew` is rejected.

### 2. Implement `RateLimiter.allow() -> bool`

Implement sliding-window rate limiting:

1. Get the current time with `time.time()`.
2. Prune `self._timestamps` to only keep entries within the window: `[t for t in self._timestamps if now - t < self.window_seconds]`.
3. If the remaining count is `>= self.max_calls`, return `False`.
4. Otherwise, append the current time to `self._timestamps` and return `True`.

The tests create a limiter with `max_calls=3, window_seconds=60` and check that the 4th call within the window is rejected.

### 3. Implement `GuardedAgent.run(question, max_steps) -> AgentResult`

This follows the same structure as the agent loop from exercises 01/02, but wraps each tool execution with safety checks:

1. Build messages: `[system_msg, {"role": "user", "content": question}]`.
2. Loop up to `max_steps`:
   - Call the API with `messages` and `self.registry.list_tools()`.
   - If `message.tool_calls`:
     - Append the assistant message to `messages`.
     - For **each** tool call:
       - **Check the allowlist**: if `self.allow_list.check(name)` is `False`, set `result` to a JSON error like `{"error": "Tool not permitted: <name>"}` and log an `AuditEntry` with `allowed=False`.
       - **Check the rate limiter**: if `self.rate_limiter.allow()` is `False`, set `result` to a JSON error like `{"error": "Rate limit exceeded"}` and log with `allowed=False`.
       - **Otherwise**: execute via `self.registry.execute(name, args)`, log with `allowed=True`.
       - Append the tool result message: `{"role": "tool", "tool_call_id": tc.id, "content": result}`.
       - Record the tool name in `tool_calls_made`.
   - Else if `message.content`: return `AgentResult` with the answer and the audit log.
3. Return `AgentResult` with `final_answer=None` if you exhaust `max_steps`.

The audit log is `self.audit_log` -- append `AuditEntry` objects as you go, then include them in the result.

## Try it

```bash
python start.py
```

The agent starts with `search_crew` blocked. Try these:

- `"How many crew in science?"` -- should succeed via `get_crew_count`. Audit shows ALLOWED.
- `"Find all engineers"` -- the model will try `search_crew`, get a "not permitted" error, and explain the denial.
- `"What's the warp status?"` -- should succeed. Watch the audit log grow.

## Tests

```bash
pytest module-02-tool-calling/exercises/03-guarded-agent/test_start.py -v
```

## Stretch goals

1. Make the rate limiter per-tool rather than global (track timestamps separately for each tool name).
2. Add a `redact()` method to `AuditEntry` that masks sensitive values in the arguments before logging.
