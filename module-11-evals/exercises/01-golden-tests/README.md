# Exercise 01 — Golden Tests

## Recap

A live chat with the Pathfinder agent is not a test. The model might call `get_crew_count` today and skip it tomorrow. **Golden-file tests** freeze a conversation: you mock the LLM with scripted `tool_calls` and a final `content` string, run the real agent loop (handlers still execute), and check that the tools and the answer match a fixture.

They are fast (no network), free (no tokens), and deterministic. Use them in CI for "did the agent still call the right tool?" — not for "is the prose nicer?"

This is the Module 2 eval-harness demo, promoted to a graded lab.

### What a golden case looks like

```json
{
  "id": "crew-count-engineering",
  "question": "How many people are in engineering?",
  "scripted_responses": [
    {"tool_calls": [{"id": "call_eng", "name": "get_crew_count", "arguments": {"department": "engineering"}}]},
    {"content": "Engineering has 2 crew members."}
  ],
  "expected_tools": [
    {"name": "get_crew_count", "arguments": {"department": "engineering"}}
  ],
  "expected_answer": "Engineering has 2 crew members."
}
```

The scripted responses *drive* the mock. The expected fields are what `score_case` checks.

## What you build

Three functions in **`start.py`**. Tools, handlers, and `make_scripted_client` are already written.

| Function | What it does |
|---|---|
| `run_case(client, case)` | Agent loop: call the client, execute tools, collect `{tools, answer}` |
| `score_case(result, case)` | Exact match on tools list and answer; list mismatches |
| `run_suite(client, cases)` | Run every case, count passed / failed |

`run_case` returns:

```python
{
    "tools": [{"name": "get_crew_count", "arguments": {"department": "engineering"}}],
    "answer": "Engineering has 2 crew members.",
}
```

`score_case` returns:

```python
{"id": "crew-count-engineering", "passed": True, "mismatches": []}
```

`mismatches` is a list of `"tools"` and/or `"answer"`.

## Step-by-step

### 1. Implement `run_case`

Same loop as Module 2, but you record every tool name + parsed arguments:

1. Messages = system prompt + `case["question"]`.
2. Call `client.chat.completions.create(model=MODEL, reasoning_effort="none", messages=messages, tools=TOOLS)`.
3. If `message.tool_calls`: for each call, `json.loads` the arguments, append to `tools`, run `HANDLERS[name](**arguments)`, append a tool-role message, loop.
4. If `message.content`: that is the answer — stop.
5. Cap with `max_steps`.

### 2. Implement `score_case`

Compare `result["tools"]` to `case["expected_tools"]` with `!=` (order and dicts must match). Compare `result["answer"]` to `case["expected_answer"]`. Collect mismatch names. `passed` is true when the list is empty.

### 3. Implement `run_suite`

For each case: `run_case` then `score_case`. Return `total`, `passed`, `failed`, and `results`.

## Try it

```bash
cd module-11-evals/exercises/01-golden-tests
python start.py
```

Uses `data/golden_cases.json` and `make_scripted_client` — no API key.

## Running Tests

```bash
pytest module-11-evals/exercises/01-golden-tests/test_start.py -v
```

## Stretch Goals

- Allow answer match to ignore trailing whitespace / case.
- Score tool *names* separately from arguments so a wrong department is a clearer failure.
- Add a golden case that expects *two* tool calls in one turn.
