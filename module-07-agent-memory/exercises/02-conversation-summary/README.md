# Exercise 02 — Conversation Summary

## Recap

Long conversations overflow the context window. The naive fix -- drop old messages -- loses important context. A better approach is **summarisation**: compress older turns into a paragraph that preserves the key points.

The pattern works like this:

```
[system prompt]
[summary of turns 1-20]     ← compressed into one message
[turn 21: user message]
[turn 22: assistant reply]
...
[turn 30: latest message]
```

When the conversation exceeds a threshold, the oldest half of messages gets summarised by the LLM and replaced with a single system message. This keeps the context window manageable while preserving continuity.

**Summarisation** calls the LLM itself:

```python
def summarise_turns(turns, client):
    formatted = "\n".join(f"{t['role']}: {t['content']}" for t in turns)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Summarise this conversation..."},
            {"role": "user", "content": formatted},
        ],
    )
    return response.choices[0].message.content
```

## What you build

A console app in **`start.py`** that extends the memory store from Exercise 1 with automatic conversation summarisation. When the session buffer gets too long, the oldest messages are compressed into a summary.

The Exercise 1 solution is provided as `memory_store.py`.

**Key components:**

| Component | Description |
|---|---|
| `summarise_turns(turns, client)` | Call OpenAI to compress a list of messages into a summary paragraph |
| `SmartSessionMemory` | Extends `SessionMemory` -- auto-summarises when messages exceed a threshold |

## Step-by-step

### 1. Import from `memory_store`

The Exercise 1 solution is provided as `memory_store.py`:

```python
from memory_store import SessionMemory, LongTermMemory, MemoryEntry, build_system_prompt, chat
```

### 2. Implement `summarise_turns`

Write a function that takes a list of message dicts and an OpenAI client, and returns a summary string:

1. Format the turns into a readable transcript
2. Call `gpt-4o-mini` with a system prompt instructing it to summarise the conversation concisely
3. Return the summary text

### 3. Implement `SmartSessionMemory`

Extend `SessionMemory` with auto-summarisation:

- Override `add(message)` to check if the message count exceeds a threshold (e.g. 10 messages)
- When triggered, take the oldest half of messages, summarise them, and replace them with a single `{"role": "system", "content": "[Summary] ..."}` message
- Store the OpenAI client reference so `add` can call `summarise_turns`
- Track the running summary so multiple summarisations accumulate

### 4. Build the interactive loop

The interactive loop uses `SmartSessionMemory` instead of `SessionMemory`, plus long-term memory from Exercise 1. The following commands are available:

| Command | Action |
|---|---|
| any text | Chat with the agent (summarisation happens automatically) |
| `/summary` | Show the current accumulated summary |
| `/turns` | Show how many messages are in the session buffer |
| `/force-summarise` | Manually trigger summarisation of the current buffer |
| `/memories` | Show long-term memories |
| `quit` | Exit |

## Try it

```bash
cd module-07-agent-memory/exercises/02-conversation-summary
python start.py
```

Have a long conversation (10+ exchanges). Watch the `/turns` count -- when it hits the threshold, summarisation triggers automatically. Use `/summary` to see the compressed history. Use `/force-summarise` to trigger it manually.

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- `summarise_turns` returns a non-empty string (mocked OpenAI call)
- `SmartSessionMemory` triggers summarisation at the threshold
- `SmartSessionMemory` preserves recent messages after summarisation
- No real OpenAI calls are made in tests

## Stretch goals

- Implement progressive summarisation: summarise the summary when it gets too long
- Add token counting instead of message counting for the threshold
- Compare summaries at different compression levels
