# Exercise 01 — Memory Store

## Recap

Agents need **memory** to be useful across turns. There are two fundamental types:

**Session memory** (short-term) holds the current conversation. It's a sliding window of messages that gets sent to the LLM on every call. Without it, the agent forgets what you just said. A cap prevents the context window from overflowing:

```python
class SessionMemory:
    def __init__(self, max_turns=20):
        self.messages = []

    def add(self, message):
        self.messages.append(message)
        if len(self.messages) > self.max_turns:
            self.messages.pop(0)  # drop oldest
```

**Long-term memory** persists facts across sessions. Each entry has an **importance score** that decays over time -- if a fact isn't reinforced, it fades. This mimics how human memory works: frequently-used facts stay strong, stale ones are forgotten:

```python
@dataclass
class MemoryEntry:
    value: str
    importance: float = 1.0   # decays each tick
    timestamp: float = ...
    forgotten: bool = False   # soft-delete
```

The agent uses long-term memory by injecting relevant facts into the system prompt. It can also **auto-detect** memorable facts from conversation and store them.

## What you build

A console app in **`start.py`** that implements both memory types and wires them into an interactive chat agent powered by OpenAI.

**Key classes/functions:**

| Component | Description |
|---|---|
| `SessionMemory` | Capped message buffer with `add` and `get_messages` |
| `LongTermMemory` | Key-value store with `remember`, `recall`, `forget`, `tick_decay` |
| `MemoryEntry` | Dataclass holding value, importance, timestamp, forgotten flag |
| `build_system_prompt` | Injects long-term memories into the system prompt |
| `chat` | Orchestrates session + long-term memory with OpenAI calls |

## Step-by-step

### 1. Implement `SessionMemory`

The session buffer holds chat messages as `{"role": ..., "content": ...}` dicts:

- `add(message)` -- append the message. If the buffer exceeds `max_turns`, drop the oldest message.
- `get_messages()` -- return the current message list.
- `clear()` -- already provided, resets the buffer.

### 2. Implement `LongTermMemory`

A dictionary-backed store where keys are topic labels and values are `MemoryEntry` objects:

- `remember(key, value, importance=1.0)` -- store a new entry (or overwrite an existing one, refreshing the timestamp).
- `recall(prefix="")` -- return all non-forgotten entries. If `prefix` is given, filter to keys that start with it. Sort by importance descending.
- `forget(key)` -- mark an entry as forgotten (soft delete). Return `True` if found.
- `tick_decay(factor=0.9)` -- multiply every non-forgotten entry's importance by `factor`. Remove entries that drop below 0.1. Return the count of removed entries.

### 3. Implement `build_system_prompt`

Build a system prompt string that includes the top long-term memories. Call `long_term.recall()` to get active memories, then format them into the prompt so the LLM is aware of stored facts.

### 4. Implement `chat`

Wire everything together:

1. Add the user's message to session memory
2. Build the system prompt (with long-term memories)
3. Construct the messages list: system prompt + session history
4. Call `client.chat.completions.create` with `gpt-4o-mini`
5. Add the assistant's response to session memory
6. Auto-detect memorable facts: make a second LLM call asking "What facts from this exchange are worth remembering long-term?" and store any results
7. Return the response text

### 5. Run the interactive loop

The `main()` function and command handling are already provided. Once you implement the core functions, these commands will work:

| Command | Action |
|---|---|
| any text | Chat with the agent |
| `/memories` | Show all long-term memories with importance scores |
| `/decay` | Apply one tick of decay to all memories |
| `/forget <key>` | Forget a specific memory by key |
| `/session` | Show session buffer stats and recent messages |
| `quit` | Exit |

## Try it

```bash
cd module-07-agent-memory/exercises/01-memory-store
python start.py
```

Chat with the agent and tell it facts about yourself. Use `/memories` to see what it stored. Apply `/decay` a few times and watch importance scores drop. Use `/forget` to remove specific memories.

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- `SessionMemory` adds messages and trims at `max_turns`
- `LongTermMemory` stores, recalls, forgets, and decays entries
- `build_system_prompt` returns a non-empty string
- No OpenAI calls are made in tests -- only the data structures are tested

## Stretch goals

- Add a `/save` and `/load` command that persists long-term memory to a JSON file
- Implement importance boosting: if the agent remembers something that already exists, increase its importance instead of overwriting
- Add semantic recall using embeddings instead of prefix matching
