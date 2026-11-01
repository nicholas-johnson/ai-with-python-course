# Exercise 01 — Golden Tests

## Recap

A live chat with the Pathfinder agent is a sample of size one. A **golden test** turns it into something you can re-run: freeze the question and the outcome you accept as correct, then run a later build of the agent and compare.

The important part is what goes in the golden file. It holds *only* the question and the accepted outcome. What the agent does comes from the build under test. Keep those two apart and "the agent stopped calling `get_ship_status`" shows up as a failing case. Put the agent's behaviour in the fixture as well and the test just confirms the script matched itself, which it will do forever.

This exercise ships two builds of the same agent so you can see the difference. `build-a` is what you released. `build-b` has had its prompt changed and has drifted. Both run against one reference:

```python
client = make_scripted_client(load_build("build-b"))
summary = run_suite(client, load_cases())
# {"total": 4, "passed": 1, "failed": 3, "results": [...]}
```

Tool calls are structured, so they exact-match cleanly. Prose does not. "Commander Elara Voss is the captain." and "The captain is Commander Elara Voss." are the same answer, and a string comparison fails one of them. That is why the harness exact-matches the tools and leaves the prose to a judge — which you build in [exercise 03](../03-llm-judge/).

### What the two builds do

| Case | `build-a` | `build-b` |
|---|---|---|
| `crew-count-engineering` | Calls `get_crew_count(department=engineering)` | Reads the wrong department |
| `ship-status-warp` | Calls `get_ship_status(system=warp)` | Skips the tool and answers from memory |
| `search-captain` | Matches the reference wording | Right facts, different words |
| `direct-answer` | Answers without a tool | Unchanged |

Two of those are real regressions. One is a false alarm that exact matching cannot tell apart from a regression.

### What a golden case looks like

```json
{
  "id": "crew-count-engineering",
  "question": "How many people are in engineering?",
  "expected_tools": [
    {"name": "get_crew_count", "arguments": {"department": "engineering"}}
  ],
  "expected_answer": "Engineering has 2 crew members."
}
```

No scripted responses, no recorded tool output. Just the question and what you accept back.

## What you build

Three functions in **`start.py`**. The ship tools, the handlers, `load_cases`, `load_build` and `make_scripted_client` are already written.

| Function | What it does |
|---|---|
| `run_case(client, case)` | Agent loop: call the client, execute tools, collect `{tools, answer}` |
| `score_case(result, case)` | Exact match on the tools list and the answer; list any mismatches |
| `run_suite(client, cases)` | Run every case, count passed and failed |

`run_case` returns what the agent actually did:

```python
{
    "tools": [{"name": "get_crew_count", "arguments": {"department": "engineering"}}],
    "answer": "Engineering has 2 crew members.",
}
```

`score_case` compares that to the reference:

```python
{"id": "crew-count-engineering", "passed": True, "mismatches": []}
```

`mismatches` is a list containing `"tools"`, `"answer"`, or both.

## Step-by-step

### 1. Implement `run_case`

This is the same tool-calling loop you wrote in Module 2, with one addition: record every tool name and its parsed arguments as you go.

1. Build the message list from `SYSTEM_PROMPT` and `case["question"]`.
2. Call `client.responses.create(model=MODEL, reasoning={"effort": "none"}, input=messages, tools=TOOLS)`.
3. Pull out the function calls with `calls = [item for item in response.output if item.type == "function_call"]`.
4. If there are any, append `response.output` to the messages. For each call, parse the arguments with `json.loads`, record `{"name": ..., "arguments": ...}`, run `HANDLERS[call.name](**arguments)`, and append a `function_call_output` item carrying the call's `call_id`. Then loop.
5. If there are none and `response.output_text` is set, that is the answer — stop.
6. Stop after `max_steps` turns either way, so a misbehaving build cannot loop forever.

### 2. Implement `score_case`

Compare `result["tools"]` to `case["expected_tools"]` with `!=`, which checks order and the argument dicts together. Compare `result["answer"]` to `case["expected_answer"]` the same way. Collect the name of each thing that differs, and set `passed` to `True` only when nothing did.

### 3. Implement `run_suite`

Call `run_case` and then `score_case` for every case, then count the results. Return `total`, `passed`, `failed`, and the list of `results`.

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

No API key needed. When your harness is working, `build-a` passes 4 of 4 and `build-b` passes 1 of 4.

## Tests

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-11-evals/exercises/01-golden-tests
pytest test_start.py -v

# Option B - uv (no activation needed):
cd module-11-evals/exercises/01-golden-tests
uv run --extra dev pytest test_start.py -v
```

The tests check:

- `run_case` records tool names and parsed arguments, and returns the final answer
- `run_case` handles a case that needs no tools at all
- `score_case` reports `tools`, `answer`, or both as mismatches
- `run_suite` counts passes and failures, including an empty suite
- `build-a` passes every case and `build-b` does not
- The golden file carries only the reference, never the agent's behaviour

## Running it against a real model

Everything above works with a live client too. Swap `make_scripted_client` for `OpenAI()` and `run_case` now reports what the *model* did rather than what a recording says it did. Keep the exact match on tool calls, and hand the prose to the judge from [exercise 03](../03-llm-judge/) instead of comparing strings:

```python
from openai import OpenAI
from start import load_cases, run_case

client = OpenAI()

def golden_eval(case):
    actual = run_case(client, case)                      # live tool calls + answer
    tools_ok = actual["tools"] == case["expected_tools"]  # structured, so exact match
    verdict = llm_judge(                                  # prose, so judge it
        client,
        question=case["question"],
        answer=actual["answer"],
        reference=case["expected_answer"],
    )
    return {"tools_ok": tools_ok, "judge": verdict}
```

Run the scripted suite on every commit, because it is free and fast. Run the live one on a schedule or behind a PR label, because it spends tokens.

## Stretch goals

- Let the answer comparison ignore trailing whitespace and case.
- Score tool *names* separately from their arguments, so a wrong department reads as a clearer failure than a missing call.
- Add a golden case that expects two tool calls in one turn, and a build that only makes one.
