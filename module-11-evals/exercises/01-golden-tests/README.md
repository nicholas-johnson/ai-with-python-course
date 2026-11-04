# Exercise 01 — Golden Tests

## Recap

A live chat with the Pathfinder agent is a sample of size one. A **golden test** turns it into something you can re-run: freeze the question and the outcome you accept as correct, then run a later build of the agent and compare.

The important part is what goes in the golden file. It holds *only* the question and the accepted outcome. What the agent does comes from the build under test. Keep those two apart and "the agent stopped calling `get_ship_status`" shows up as a failing case. Put the agent's behaviour in the fixture as well and the test just confirms the script matched itself, which it will do forever.

This exercise ships two builds of the same agent so you can see the difference. `build-a` is what you released. `build-b` has had its prompt changed and has drifted. Both run against one reference:

```python
client = make_scripted_client(load_build("build-b"))
summary = run_suite(client, load_cases(), make_canned_judge("build-b"))
# {"total": 4, "passed": 2, "failed": 2, "suite": 0.64, "results": [...]}
```

Tool calls are structured, so they exact-match cleanly: 0 or 1. Prose does not. "Commander Elara Voss is the captain." and "The captain is Commander Elara Voss." are the same answer, and a string comparison fails one of them. So the harness exact-matches the tools and hands the prose to a **judge**, which scores correctness, completeness and relevance on a 1–5 rubric — the same judge you build in [exercise 03](../03-llm-judge/).

That makes a case score continuous rather than pass/fail. Normalise each rubric score onto `[0, 1]`, average the four criteria for a per-case score, and average those for the suite:

```
suite = mean over cases of ( mean over criteria of s )
```

A case passes when its score reaches `PASS_THRESHOLD` (0.8). The judge verdicts are canned here, so the whole lab still runs with no API key.

### What the two builds do

| Case | `build-a` | `build-b` | `build-b` score |
|---|---|---|---|
| `crew-count-engineering` | Calls `get_crew_count(department=engineering)` | Reads the wrong department | 0.31 |
| `ship-status-warp` | Calls `get_ship_status(system=warp)` | Skips the tool and answers from memory | 0.25 |
| `search-captain` | Matches the reference wording | Right facts, different words | 1.00 |
| `direct-answer` | Answers without a tool | Unchanged | 1.00 |

Two of those are real regressions, and they score low enough to fail. `search-captain` is the one a string comparison gets wrong: the facts are right and only the clause order moved, so the judge gives it full marks and it passes.

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

Three functions in **`start.py`**. The ship tools, the handlers, `load_cases`, `load_build`, `make_scripted_client`, `make_canned_judge` and `normalise` are already written.

| Function | What it does |
|---|---|
| `run_case(client, case)` | Agent loop: call the client, execute tools, collect `{tools, answer}` |
| `score_case(result, case, judge)` | Score four criteria in `[0, 1]` and average them |
| `run_suite(client, cases, judge)` | Run every case, count passes, average the scores |

`run_case` returns what the agent actually did:

```python
{
    "tools": [{"name": "get_crew_count", "arguments": {"department": "engineering"}}],
    "answer": "Engineering has 2 crew members.",
}
```

`score_case` scores that against the reference:

```python
{
    "id": "crew-count-engineering",
    "score": 0.31,
    "criteria": {"tools": 0.0, "correctness": 0.0, "completeness": 0.25, "relevance": 1.0},
    "passed": False,
    "explanation": "Says 1 crew member; the reference says 2.",
}
```

The `criteria` dict is where the diagnosis lives. A score of 0.31 tells you the case failed; `tools: 0.0` tells you it called the wrong tool, and `correctness: 0.0` tells you the answer was wrong too.

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

Call `judge(case["id"], case["question"], result["answer"], case["expected_answer"])`. It returns 1–5 scores for `correctness`, `completeness` and `relevance`, plus an `explanation`.

Then build the `criteria` dict. The `tools` criterion is `1.0` when `result["tools"] == case["expected_tools"]` and `0.0` otherwise — comparing the lists with `==` checks order and the argument dicts together, and tool calls are structured, so they either match or they do not. Each judge criterion is `normalise(verdict[name])`, which maps 1–5 onto `[0, 1]`.

`score` is the mean of the criteria values, and `passed` is `score >= PASS_THRESHOLD`.

### 3. Implement `run_suite`

Call `run_case` and then `score_case` for every case, then aggregate. Return `total`, `passed`, `failed`, the mean of the per-case scores as `suite`, and the list of `results`. Guard the empty suite so it reports `0.0` instead of dividing by zero.

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

No API key needed. When your harness is working, `build-a` scores 1.00 and passes 4 of 4; `build-b` scores 0.64 and passes 2 of 4.

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
- `normalise` maps the 1–5 rubric onto `[0, 1]`
- `score_case` returns the mean of its four criteria, all within `[0, 1]`
- A wrong tool call costs a whole criterion, and a paraphrased answer still passes
- `run_suite` counts passes and averages the scores, including an empty suite
- `build-a` scores 1.00 on every case and `build-b` scores lower
- The golden file carries only the reference, never the agent's behaviour

## Running it against a real model

Two things are simulated here: the build under test and the judge. Swap either for a real client and nothing about the harness changes.

Pass `OpenAI()` instead of `make_scripted_client(...)` and `run_case` reports what the *model* did rather than what a recording says it did. Replace `make_canned_judge(...)` with a judge backed by `llm_judge` from [exercise 03](../03-llm-judge/), which has the same signature:

```python
from openai import OpenAI
from start import load_cases, run_suite

client = OpenAI()

def live_judge(case_id, question, answer, reference):
    return llm_judge(client, question=question, answer=answer, reference=reference)

summary = run_suite(client, load_cases(), live_judge)
```

Run the scripted suite on every commit, because it is free and fast. Run the live one on a schedule or behind a PR label, because it spends tokens — one judge call per case on top of the agent itself.

## Stretch goals

- Weight the criteria instead of averaging them equally: replace the `1/M` with weights that sum to 1, so a wrong tool call costs more than a terse answer. That is what the scorecard in [exercise 05](../05-eval-compare/) does.
- Score tool *names* separately from their arguments, so a wrong department reads as a clearer failure than a missing call.
- Add a golden case that expects two tool calls in one turn, and a build that only makes one.
- Tune `PASS_THRESHOLD`. At what floor does `build-b`'s paraphrase case start failing, and is that the behaviour you want?
