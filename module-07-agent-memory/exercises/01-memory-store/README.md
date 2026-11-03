# Exercise 01 — Memory Store

## Recap

An LLM remembers nothing between calls. Memory is two moves you build yourself: **write** facts to a store outside the model, and **select** them back into the next prompt.

Selecting is a retrieval problem, so it uses the tools from Module 5. Memories go into a vector collection; the current turn is the query. Similarity alone is not enough to rank them, so you over-fetch and score on three signals:

```python
similarities = [1.0 - d for d in results["distances"][0]]   # cosine distance -> similarity
relevances = normalise(similarities)                        # spread across [0, 1]

recency = 0.5 ** (age_days / HALF_LIFE_DAYS)                # decay, as a weight
score = 0.6 * relevance + 0.25 * recency + 0.15 * importance
```

Writing has three possible outcomes, not one:

| Outcome | When | What you do |
| ------- | ---- | ----------- |
| `store` | Genuinely new | Write it |
| `replace` | It contradicts something held — a changed preference, a settled tab | Write it, then supersede the old one |
| `skip` | Something held already says this | Write nothing |

Both `supersede` and `forget` are soft deletes: `active` goes to `False` and the row stays. The content stops reaching the model while the record that it existed survives, which is what an audit trail needs.

## The scenario

You are building **BARKEEP** — the AI bartender at **The Nebula's Edge**, a cantina on Relay Station Omicron. A good bartender remembers every regular's usual, their allergies, and who still owes for last rotation. Memory is the entire premise: "the usual" only works if you know what the usual is.

The cantina has more than one regular, so the store is namespaced. Zara's memories must never surface while you are serving Tanaka — the `where` filter on every query is the only thing standing between you and a privacy incident.

## What you build

A console app in **`start.py`**: a Chroma-backed semantic memory store wired into an interactive chat agent.

| Component | Description |
| --- | --- |
| `embed` | One string to one embedding vector |
| `normalise` | Min-max the similarities across the candidate set |
| `recency_weight`, `score_memory` | Half-life decay, and the weighted blend of the three signals |
| `MemoryStore.remember` | Write one memory with its metadata |
| `MemoryStore.recall` | Over-fetch, score, sort, return the top k |
| `MemoryStore._deactivate` | The soft delete behind `supersede` and `forget` |
| `propose_memories` | Structured call deciding what a turn is worth keeping |
| `write_memories` | Branch on store / replace / skip |
| `build_system_prompt` | Persona plus the recalled memory block |
| `chat` | Recall, answer, then write |

`resolve` — the structured call that chooses between store, replace, and skip — is given to you. What you do with its answer is the interesting part.

## Step-by-step

### 1. The scoring functions

Start here, because the tests for them need nothing but Python.

- `embed(text, client)` — call `client.embeddings.create(model=EMBED_MODEL, input=[text])` and return `response.data[0].embedding`.
- `normalise(similarities)` — min-max across the list. Return `[]` for an empty list, and `1.0` for every entry when they are all equal. Without this step, raw cosine similarities sit in a band around 0.03 to 0.38 while recency spans 0 to 1, and recency wins every ranking.
- `recency_weight(written_at, now)` — `0.5 ** (age_days / HALF_LIFE_DAYS)`, with age floored at zero.
- `score_memory(relevance, written_at, importance, now)` — return `(recency, combined)` using the three weight constants.

### 2. `MemoryStore.remember`

Call `self.collection.add` with the id, the embedding, the document text, and a metadata dict holding `patron`, `kind`, `importance`, `written_at`, `active=True`, and `superseded_by=""`.

Chroma metadata values have to be `str`, `int`, `float`, or `bool` — that is why `superseded_by` starts as an empty string rather than `None`.

### 3. `MemoryStore.recall`

1. Query with `n_results=max(k * 4, k)` — over-fetch, because you are about to rescore.
2. Filter with `where={"$and": [{"patron": {"$eq": patron}}, {"active": {"$eq": True}}]}`. Both clauses matter: the first is the namespace, the second hides soft-deleted rows.
3. Return `[]` when nothing comes back.
4. Turn distances into similarities, normalise them, score each candidate, sort descending, return the first `k`.

### 4. `MemoryStore._deactivate`

Fetch the row by id, return `False` if it is not there, then copy the metadata, set `active=False` and `superseded_by`, and `update` it. `supersede` and `forget` are already written on top of this.

### 5. `propose_memories` and `write_memories`

`propose_memories` is a structured call with `text_format=WriteDecision`. Most turns should return an empty list — that is the correct answer for "what's on tap tonight?".

`write_memories` is where the three outcomes live. For each candidate:

1. `store.recall(candidate.text, patron=patron, k=3)` — the neighbours. A contradiction or a duplicate is always semantically close to the new fact, so this is where it will be.
2. `resolve(...)` for the decision.
3. On `skip`, print a note and move on.
4. Otherwise `remember` it, and on `replace` supersede `neighbours[decision.target].memory_id`.

### 6. `build_system_prompt` and `chat`

The prompt is `PERSONA` plus a bulleted block of recalled memory text. `chat` recalls against the user's message, answers with `[system, *thread]`, then writes. Writing on the hot path costs the user a second call; a production chat would do it in the background after streaming the reply.

## Try it

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-07-agent-memory/exercises/01-memory-store
python start.py

# Option B - uv (no activation needed):
cd module-07-agent-memory/exercises/01-memory-store
uv run python start.py
```

| Command | Action |
| --- | --- |
| any text | Chat with BARKEEP |
| `/memories` | Every live memory for the current patron |
| `/recall <query>` | Run recall and show the score breakdown |
| `/forget <n>` | Soft-delete memory `n` from the `/memories` listing |
| `/patron <name>` | Switch patrons — fresh conversation, separate memories |
| `quit` | Exit |

Worth doing in order: tell BARKEEP your usual, then tell it again in different words and watch the writer skip it. Change your mind about something and watch the old memory get superseded. Then `/patron tanaka` and check that none of Zara's memories follow you.

## Tests

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-07-agent-memory/exercises/01-memory-store
pytest test_start.py -v

# Option B - uv (no activation needed):
cd module-07-agent-memory/exercises/01-memory-store
uv run --extra dev pytest test_start.py -v
```

The tests need no API key and no ChromaDB — the collection is a dict-backed stub with canned distances and embeddings come from a mock. They check that:

- `normalise` spreads candidates across `[0, 1]` and survives empty and all-equal input
- `recency_weight` halves once per half-life
- `score_memory` is the weighted sum of the three signals
- `remember` and `recall` round-trip a memory with its metadata
- recall is namespaced per patron, respects `k`, and ranks a relevant old memory above a fresh irrelevant one
- `forget` stops recall but leaves the row, and `supersede` records what replaced it
- `build_system_prompt` carries both the persona and the recalled text

## Stretch goals

- Add `/why <query>`: show every candidate the over-fetch returned, including the ones that lost, with their three component scores. Useful when recall surprises you.
- Tune the weights. Set `RECENCY_WEIGHT` to 0.6 and find a query where the ranking becomes obviously wrong.
- Write memories in the background with `asyncio` so the reply streams first and the write lands after.
- Add a `kind` boost: constraints outrank preferences at equal relevance, because serving someone an allergen is worse than forgetting their usual.
