# Exercise 03 — Cost Controls

## Recap

An agent loop has no natural stopping point. A prototype that answers one question for a fraction of a cent becomes a retry storm or a planning loop that calls the model forty times, and the failure mode is a bill rather than a crash you would notice.

Three levers, in rough order of how much they save:

| Lever | What it does |
|---|---|
| **Model tiering** | Send lookups to a cheap model and keep the expensive one for reasoning |
| **Caching** | Do not pay twice for the same question |
| **Budgets** | Refuse work once the allowance is spent |

### Budget in tokens, report in dollars

Every response comes back with `usage.input_tokens` and `usage.output_tokens`. That is the number to enforce on, because it is exact and immediate. Dollars are derived from it — useful for a report, awkward as a limit, since the rates change and differ per model.

Note that **output tokens cost roughly five times what input tokens cost**. Reasoning tokens are billed as output, which is why `reasoning={"effort": "none"}` is a cost decision and not only a latency one.

### Why tiering is the big lever

`gpt-6-luna` is around 20x cheaper than `gpt-6-sol` on the rates in `COST_PER_1K`. Most queries in a real system are lookups — "who is on duty", "what is the hull status" — and a cheap model answers those as well as an expensive one. The router in this exercise uses a crude keyword check. A production one usually calls a cheap model to do the classification, which is itself a good argument for the pattern.

### Why the cache checks before the budget

In `answer_query`, the cache lookup comes *before* the budget check. A cached answer costs nothing, so there is no reason to refuse it just because the session allowance is gone. Getting this order backwards means a user who repeats a question gets turned away for free work.

## What you build

Three pieces in **`start.py`**. `CostTracker.summary`, `PromptCache.hit_rate`, the scripted client, and `answer_query` are written for you.

| Piece | What it does |
|---|---|
| `CostTracker.record` / `.within_budget` | Accumulate tokens and USD; report whether there is room left |
| `classify_complexity` / `choose_model` | Label a query, then route it to the cheap or the premium model |
| `PromptCache.key` / `.get` / `.set` | Hash `(model, prompt)`, serve repeats, count hits and misses |

## Step-by-step

### 1. `CostTracker`

`record(model, input_tokens, output_tokens)` looks up the per-1K rates, defaults to the `PREMIUM_MODEL` entry for a model it does not recognise, and returns the cost of this one call:

```python
cost = input_tokens / 1000 * rates["input"] + output_tokens / 1000 * rates["output"]
```

Defaulting *high* on an unknown model is deliberate. A model name you have not priced yet should show up as an overestimate you notice, not as free.

Add the token total to both `session_tokens` and `daily_tokens`, add the cost to `session_cost_usd`, increment `calls`, and return the cost.

`within_budget()` is true while **both** totals are strictly under their budgets. Strictly — a session that has used exactly its allowance is finished, not eligible for one more call.

### 2. `classify_complexity` and `choose_model`

Lowercase the query and return `"simple"` if any entry in `SIMPLE_MARKERS` appears in it, otherwise `"complex"`. Then `choose_model` maps `"simple"` to `CHEAP_MODEL` and anything else to `PREMIUM_MODEL`.

Defaulting to the expensive model when unsure is the right way round: a lookup answered by the premium model costs a fraction of a cent, while a reasoning task handed to the cheap model produces a wrong answer.

### 3. `PromptCache`

`key(model, prompt)` normalises with `prompt.strip().lower()`, then returns `hashlib.sha256(f"{model}:{normalised}".encode()).hexdigest()`.

The model belongs in the key because the same question answered by two models gives two different results, and they must not collide. The normalisation is what stops `"Warp status?"` and `"  warp status? "` from occupying two entries and halving your hit rate.

`get` increments `hits` or `misses` and returns the answer or `None`. `set` stores under the same key.

## Try it

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-12-productionisation/exercises/03-cost-controls
python start.py

# Option B - uv (no activation needed):
cd module-12-productionisation/exercises/03-cost-controls
uv run python start.py
```

No API key — a scripted client returns canned answers with usage counts in the real shape. The session budget is set deliberately low so the last query is refused:

```
  gpt-6-luna  $0.00001  What is the warp core efficiency?
  gpt-6-luna  $0.00001  Who is the chief engineer?
  gpt-6-luna  cached    What is the warp core efficiency?
  gpt-6-sol   $0.00013  Compare the ion storm damage against the hull stress model a
  refused (budget spent)  How many crew are in engineering?
```

Note the premium call costs about ten times the cheap ones, on a query that genuinely needs it.

## Running Tests

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pytest module-12-productionisation/exercises/03-cost-controls/test_start.py -v

# Option B - uv (no activation needed):
uv run --extra dev pytest module-12-productionisation/exercises/03-cost-controls/test_start.py -v
```

## Stretch Goals

- Give the cache a TTL so ship telemetry answers expire after a minute while definitions live for a day.
- Replace the keyword router with a `gpt-6-luna` call that classifies the query, and measure whether the routing saves more than the classification costs.
- Track budgets per user rather than per session, so one person cannot spend the deployment's daily allowance.
- Add a `reserve(estimated_tokens)` that holds budget before the call and settles against the real usage afterwards — the check in this exercise can be beaten by one very large request.
- Swap the exact-match cache for the semantic cache from [Module 13](../../../module-13-edge-topics/exercises/09-semantic-cache/), which matches "warp status" to "how is the warp core".
