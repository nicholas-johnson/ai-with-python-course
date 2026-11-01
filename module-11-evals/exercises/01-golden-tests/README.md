# Exercise 01 — Golden Tests

## Recap

A live chat with the Pathfinder agent is not a test. But there are two different things to test, and it helps to keep them apart.

**This lab builds an agent-loop regression test.** You mock the LLM with scripted `tool_calls` and a final `content` string, run the real agent loop (handlers still execute), and check that the tools and the answer match a fixture. Because the script already contains the tool call and the answer, this is really a test of *your loop* — did it parse arguments, dispatch the right handler, round-trip `call_id`, and stop on the final text? It is fast (no network), free (no tokens), and deterministic, so it belongs in CI on every commit.

**A real golden test is the other thing.** It freezes the questions and the outputs you accept as correct, then runs the **real** model and compares. Tool calls exact-match; the prose is graded by an LLM-as-judge or a human. That is what catches "the agent stopped calling `get_ship_status`" — a regression the scripted mock cannot see, because no model runs. See [Real golden eval](#real-golden-eval-optional-needs-a-key) below.

This is the Module 2 eval-harness demo, promoted to a graded lab.

### What this catches / what it doesn't

| The scripted mock catches | Only a live golden eval catches |
|---|---|
| A broken dispatcher (wrong handler for a tool name) | The model choosing the wrong tool |
| A handler that returns the wrong count/data | The model skipping a tool call it used to make |
| A loop that drops `call_id` or never stops | Prose quality drifting on a prompt change |

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
2. Call `client.responses.create(model=MODEL, reasoning={"effort": "none"}, input=messages, tools=TOOLS)`.
3. Collect `calls = [item for item in response.output if item.type == "function_call"]`. If there are any: add `response.output` to `messages`, then for each call `json.loads` the arguments, append to `tools`, run `HANDLERS[call.name](**arguments)`, append a `function_call_output` item with the call's `call_id`, and loop.
4. Otherwise `response.output_text` is the answer — stop.
5. Cap with `max_steps`.

### 2. Implement `score_case`

Compare `result["tools"]` to `case["expected_tools"]` with `!=` (order and dicts must match). Compare `result["answer"]` to `case["expected_answer"]`. Collect mismatch names. `passed` is true when the list is empty.

### 3. Implement `run_suite`

For each case: `run_case` then `score_case`. Return `total`, `passed`, `failed`, and `results`.

## Try it

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-11-evals/exercises/01-golden-tests
python start.py

# Option B - uv (no activation needed):
cd module-11-evals/exercises/01-golden-tests
uv run python start.py
```

Uses `data/golden_cases.json` and `make_scripted_client` — no API key.

## Running Tests

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pytest module-11-evals/exercises/01-golden-tests/test_start.py -v

# Option B - uv (no activation needed):
uv run --extra dev pytest module-11-evals/exercises/01-golden-tests/test_start.py -v
```

## Real golden eval (optional, needs a key)

The functions you just built are half of a real golden eval. Swap the scripted client for a live one and `run_case` now reports what the **model** actually did — keep the exact-match on tool calls, and hand the prose to the judge from [exercise 03](../03-llm-judge/) instead of comparing strings. No new graded function; this stays out of CI because it spends tokens.

```python
from openai import OpenAI
from start import run_case  # exact-match tool calls against a live client
# llm_judge lives in exercises/03-llm-judge/solution.py

client = OpenAI()  # real model, not make_scripted_client

def golden_eval(case):
    actual = run_case(client, case)                      # live tool calls + answer
    tools_ok = actual["tools"] == case["expected_tools"] # structured → exact match
    verdict = llm_judge(                                 # prose → judge, not ==
        client,
        question=case["question"],
        answer=actual["answer"],
        reference=case["expected_answer"],
    )
    return {"tools_ok": tools_ok, "judge": verdict}
```

Run the scripted harness test on every commit; run this on a schedule or a PR label.

## Stretch Goals

- Allow answer match to ignore trailing whitespace / case.
- Score tool *names* separately from arguments so a wrong department is a clearer failure.
- Add a golden case that expects *two* tool calls in one turn.
