# Exercise 02 — Compaction

## Recap

Exercise 01 handled memory: durable facts written to a store and selected back when relevant. This exercise handles the other half of the budget problem — **history**, the one component that grows every turn and has no natural ceiling. Turn fifty resends turns one through forty-nine.

Dropping the oldest messages is the obvious fix and the wrong one. The oldest turns are where the decisions were made. "Charge everything to the ship's account" was agreed on turn three; truncate turn three and BARKEEP starts asking for credits again.

**Compaction** replaces a span of history with a summary that deliberately preserves the load-bearing parts. You name them rather than hoping the summary keeps them:

```python
class Anchor(BaseModel):
    kind: Literal["decision", "open_task", "constraint"]
    text: str


class Compaction(BaseModel):
    summary: str
    anchors: list[Anchor]
```

Three things go wrong if you are careless, and all three are in this exercise:

| Failure | What happens | The fix here |
| ------- | ------------ | ------------ |
| Orphaned tool pair | A `function_call` without its `function_call_output` is an API error | `safe_split` walks the boundary back |
| Broken cache prefix | Prompt caching keys on the longest identical prefix, so rewriting the front costs full price on every later call | The system prompt is assembled outside the thread and never rewritten |
| Summary-of-summary drift | Compacting a compaction bleeds detail away a pass at a time | `carried` anchors are re-emitted verbatim |

## The scenario

Same cantina, same BARKEEP, but now it is a long evening. The Pathfinder crew has been in for hours, decisions have been made, a tab is outstanding, and the conversation has long since outgrown a sensible prompt.

Exercise 01's memory store comes along as `memory_store.py`, so recall keeps working while you deal with history. Swap in your own version if you would rather.

## What you build

Compaction in **`start.py`**, wired into the chat loop so it fires on a budget trigger.

| Component | Description |
| --- | --- |
| `count_tokens` | Token cost of a message list, tool items included |
| `safe_split` | A split boundary that never separates a tool call from its output |
| `summarise` | Structured call returning a summary plus anchors |
| `render_block` | The single system message that replaces the old span |
| `compact` | Budget trigger, split, summarise, rebuild, report |
| `build_system_prompt` | Persona plus recalled memories |
| `chat` | Recall, compact if over budget, answer |

## Step-by-step

### 1. `count_tokens`

Encode each message's text with `ENCODING` and add `MESSAGE_OVERHEAD` for the role and delimiters.

The catch: a Responses API item does not always carry text in `content`. A `function_call` has `arguments` and `name`; a `function_call_output` has `output`. Miss those and tool calls count as free, which is exactly backwards — tool output is often the biggest thing in the thread.

### 2. `safe_split`

Clamp the index into range, then walk backwards while the message at that index is a `function_call_output`. Mind the ends: the index can legitimately equal `len(messages)`, and indexing there will raise.

### 3. `summarise`

Flatten the span into a transcript, then one structured call with `text_format=Compaction`. Note what `COMPACT_PROMPT` asks for: at most five anchors, each a short clause. Without that cap the model writes an exhaustive anchor list that is as long as the conversation it replaced, and you save nothing.

### 4. `render_block`

Concatenate the carried anchors with the new ones, then emit the summary followed by one line per kind that has entries. Carried anchors go in verbatim — that is the whole defence against drift.

### 5. `compact`

1. Return `(messages, None)` when you are already under budget or the thread is no longer than `keep_recent`. No model call unless you are genuinely over — compaction is a trigger, not a scheduled job.
2. Split at `len(messages) - keep_recent`, passed through `safe_split`.
3. Summarise the old span, render it into one system message, and return `[block, *recent]` with a `CompactionReport`.

### 6. `chat`

Recall, append the user turn, compact, answer, append the reply. One subtlety: `compact` returns a new list, so write it back with `thread[:] = compacted` rather than rebinding the local name, or the caller keeps the old thread.

## Try it

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-07-agent-memory/exercises/02-compaction
python start.py

# Option B - uv (no activation needed):
cd module-07-agent-memory/exercises/02-compaction
uv run python start.py
```

| Command | Action |
| --- | --- |
| any text | Chat with BARKEEP |
| `/seed` | Load a canned long evening, including a tool call pair |
| `/budget` | Current token count against the budget |
| `/thread` | The message list as it stands |
| `/anchors` | Every anchor carried so far |
| `/compact` | Force a compaction now |
| `quit` | Exit |

Try this: `/seed`, then `/budget` to see you are over, then `/compact` and watch the boundary move off the tool output. `/thread` shows the block that replaced eleven messages. Then ask "who is paying tonight?" — the answer should still be the ship's account, because it survived as an anchor.

## Tests

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-07-agent-memory/exercises/02-compaction
pytest test_start.py -v

# Option B - uv (no activation needed):
cd module-07-agent-memory/exercises/02-compaction
uv run --extra dev pytest test_start.py -v
```

No API key needed — `responses.parse` is mocked to return a fixed `Compaction`. The tests check that:

- `count_tokens` counts chat messages and tool items alike
- `safe_split` leaves a clean boundary alone, moves off a tool output, and clamps out-of-range input
- `render_block` labels each anchor kind, omits empty ones, and re-emits carried anchors
- `compact` makes no model call under budget, replaces the old span with one block, keeps the recent messages verbatim, and never orphans a tool pair

## Stretch goals

- Compact in a loop until the thread is actually under budget. One pass often gets close but not all the way.
- Deduplicate anchors before rendering: after three passes you will have the same decision three times.
- Track how many times a span has been compacted and log it. Watch the detail degrade generation by generation.
- Write the pre-compaction thread to a JSONL file first. When an agent answers oddly after a compaction, that file is the only way to find out what it used to know.
