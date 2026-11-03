# Exercise 03 — Memory MCP Server

## Recap

Exercise 01 built the write and select halves of memory. Exercise 02 built compaction. Both live inside the agent process, which means they belong to that one agent and vanish when it exits.

This exercise puts both behind a single MCP server. Nothing about the mechanics changes — the same scoring, the same anchors — but the boundary moves. The agent stops owning its memory and starts calling a service that owns it.

That boundary buys three things:

- **Other agents.** The concierge desk and the kitchen can call `recall` for the same patron without a line of shared code.
- **Restarts.** The thread of record lives on the server, so a crashed agent reconnects and asks what it was doing.
- **One place to fix things.** Change the scoring weights or the anchor prompt once, and every caller gets it.

## The scenario

The Nebula's Edge is expanding, and management wants BARKEEP's memory to be station infrastructure rather than one bartender's private notebook. So memory and compaction move behind MCP, and BARKEEP becomes a client of them.

Exercise 01's store arrives as `memory_store.py` and Exercise 02's compaction as `compaction.py`. Swap in your own if you would rather.

## Two families of tools, two different callers

This is the part worth slowing down for. The server exposes both families, but they are not used the same way:

| Family | Tools | Who calls it | Why |
| --- | --- | --- | --- |
| Memory | `remember`, `recall`, `forget`, `list_memories` | the model | Only the model knows a patron just said something durable |
| Compaction | `append_turn`, `thread_budget`, `compact_thread`, `get_thread`, `get_anchors` | the harness | The thread has to be recorded and compacted whatever the model decides |

Compaction is not a judgement call. If it were a tool the model chose to use, it would forget to use it exactly when the context was fullest. So the harness logs each turn, checks the budget, and compacts — and the model never sees it happen.

One consequence worth noticing: after a compaction the harness has to **rebuild the model's context** from the server's thread. Compact on the server and leave the agent's own message list alone, and you have saved tokens in the one place that was not costing you anything.

## What you build

Two files, both scaffolded:

| File | What it is |
| --- | --- |
| `server.py` | The MCP server: nine tools over the store and the compactor |
| `start.py` | A console agent that connects over stdio and runs a tool-calling loop |

Server side:

| Tool | Returns |
| --- | --- |
| `remember(patron, text, kind)` | Confirmation, with the new id |
| `recall(patron, query, k)` | Ranked memories with scores and ids |
| `forget(memory_id)` | Confirmation, or that there was nothing to forget |
| `list_memories(patron)` | Every live memory for a patron |
| `append_turn(thread_id, role, text)` | New message count and token cost |
| `thread_budget(thread_id, budget_tokens)` | Token count, and whether it is over |
| `compact_thread(thread_id, budget_tokens, keep_recent)` | The report and the new block |
| `get_thread(thread_id)` | The thread as JSON |
| `get_anchors(thread_id)` | Decisions, open tasks, and constraints so far |

Client side: `mcp_to_openai_tools`, `call_text`, `run_turn`, `rebuild_context`, `record_turns`.

## Step-by-step

### 1. The memory tools

Thin wrappers. `remember` calls `store.remember`, `recall` calls `store.recall` and formats the results, `forget` reports whether it found anything.

Two things matter more than they look:

- **The docstring is the tool description.** MCP sends it to the model, so it is the only thing telling the agent when to reach for the tool. "Store a fact" gets you a transcript. Naming what counts as durable — a usual order, an allergy, an unpaid tab — gets you memories worth keeping.
- **Return ids.** `forget` takes an id, so `recall` and `list_memories` have to hand them out. A tool the model cannot address is a tool it cannot use.

### 2. The compaction tools

The server owns the thread, one list per `thread_id`, and the anchors carried for it.

`append_turn` and `thread_budget` are bookkeeping. `thread_budget` has to say "over budget" in so many words when it is over — the client reads that string, which is the kind of shortcut a text-returning tool invites. `compact_thread` calls the `compact` you wrote in Exercise 02 and passes the carried anchors in.

### 3. `merge_anchors`

Not a tool, a helper, and the one piece of genuinely new logic here.

Every pass re-reads the previous compaction block, so the model re-extracts anchors it has already seen and your anchor list fills with near-copies of the same decision. Compare on kind and text with case and whitespace stripped, and keep only what is new. `COMPACT_PROMPT` also now tells the model that anchors in an `[Earlier conversation]` block are already preserved, which stops most of the repetition before it reaches you. Belt and braces: the prompt asks, the service enforces.

### 4. `mcp_to_openai_tools` and `call_text`

MCP's `input_schema` is already JSON Schema, so conversion is a rename: `{"type": "function", "name": ..., "description": ..., "parameters": tool.input_schema}`.

`call_text` pulls `result.content[0].text` out of a tool result, and copes with an empty result rather than raising mid-turn.

### 5. `run_turn`

The tool-calling loop from Module 2, with `await call_text(...)` where the local function used to be. Tool results go back as `function_call_output` keyed by `call_id`. Print the calls — watching the agent decide to reach for memory is most of what this exercise has to show.

### 6. `rebuild_context` and `record_turns`

`record_turns` logs both sides of the turn, checks the budget, and compacts when it has to. `rebuild_context` then replaces the model's context with the server's thread, keeping `messages[0]` — your system prompt, which is local and must stay byte-identical for the prompt cache.

Assign into the list with `messages[:] = ...` rather than rebinding the name. The caller is holding the same list.

## Try it

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-07-agent-memory/exercises/03-memory-server
python start.py

# Option B - uv (no activation needed):
cd module-07-agent-memory/exercises/03-memory-server
uv run python start.py
```

The client spawns `server.py` itself, so there is nothing to start separately. To poke the server on its own, `mcp dev server.py` opens the Inspector and lets you call each tool by hand.

| Command | Action |
| --- | --- |
| any text | Chat with BARKEEP (tool calls print inline) |
| `/tools` | The tools discovered over MCP |
| `/seed` | Load a canned long evening into the thread |
| `/memories` | Every live memory for the patron |
| `/budget` | Thread tokens against the budget |
| `/anchors` | Anchors carried so far |
| `/compact` | Force a compaction now |
| `quit` | Exit |

Try this. `/seed`, then `/compact`, and watch the thread drop by about a third. Then ask "whose account is tonight on, and what must I keep away from Tanaka?" — the agent answers both from the compaction block, having never seen the eight messages it replaced.

Then tell it something durable about yourself and watch `remember` fire, `/memories` to see it stored, and `/forget` through the agent to take it back out.

## Tests

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd module-07-agent-memory/exercises/03-memory-server
pytest test_start.py -v

# Option B - uv (no activation needed):
cd module-07-agent-memory/exercises/03-memory-server
uv run --extra dev pytest test_start.py -v
```

The client tests mock the model and the MCP session, so no API key is needed for them. The server tests import `server.py`, which builds an OpenAI client, so those want a key in `.env` — but they make no calls.

The tests check that:

- the server registers both families of tools, and every tool has a description
- `remember` asks for a patron, and `compact_thread` for a thread id and a budget
- `mcp_to_openai_tools` converts a tool and preserves its schema
- `call_text` returns the tool text and survives an empty result
- `run_turn` returns the answer, feeds tool output back keyed by `call_id`, and gives up rather than looping forever
- `record_turns` logs both sides, leaves a thread under budget alone, and compacts and rebuilds the context when it is over
- `rebuild_context` keeps the system prompt in front of the service's thread

## Stretch goals

- Expose the server over HTTP instead of stdio and point two clients at it at once. Watch what happens when both compact the same thread.
- Persist the threads and anchors the way the memories are persisted. The memories survive a restart; the thread does not.
- Add a `write_turn` tool that decides for itself whether a turn is worth remembering, using the `WriteDecision` extraction from the demo, so the model stops being the one who has to judge.
- Scope the tools: a `patron` argument the caller chooses is also a patron argument the caller can get wrong. Bind the identity to the session instead and see how much simpler the tool signatures get.
