# Module 7 — Agent Memory

> An LLM has no memory between API calls. Every request is stateless — the model sees only the messages you send. "Memory" is a design pattern: you store information externally and inject it into the prompt when relevant. This module gives the agent a memory system with short-term session recall, long-term profile storage, and summarisation to keep conversations within token budgets.

## Learning goals

- Distinguish **short-term** (session) and **long-term** (profile) memory.
- Implement **summarisation** to compress conversation history under token budgets.
- Model **memory decay** and explicit "do not remember" controls for privacy.
- Expose memory as **MCP tools** so any agent can use it.

---

## Why agents need memory

Without memory, a crew member who says "As I mentioned earlier, the reactor is unstable" gets a confused response — the agent has no "earlier" to reference. With memory, the agent retrieves the previous conversation and responds in context.

---

## Short-term memory — session context

Session memory holds the current conversation. It is the list of messages from the current chat session, capped at a length or token budget so it fits in the context window.

```python
class SessionMemory:
    def __init__(self, max_turns: int = 50, max_tokens: int = 4000):
        self.messages: list[dict] = []
        self.max_turns = max_turns
        self.max_tokens = max_tokens

    def add(self, message: dict):
        self.messages.append(message)
        self._trim()

    def _trim(self):
        while len(self.messages) > self.max_turns:
            self.messages.pop(0)
        while self._token_count() > self.max_tokens:
            self.messages.pop(0)
```

When the session exceeds the budget, the oldest messages are dropped. The system prompt is always preserved — it defines the agent's behaviour. Recent turns are more valuable than old ones, so FIFO eviction is the right default.

---

## Long-term memory — profiles and facts

Long-term memory persists across sessions. When Commander Voss says "I prefer concise briefings," the agent stores that preference and applies it in every future conversation.

```python
class LongTermMemory:
    def __init__(self):
        self._store: dict[str, MemoryEntry] = {}

    def remember(self, key: str, value: str, importance: float = 1.0):
        self._store[key] = MemoryEntry(
            value=value,
            importance=importance,
            last_accessed=time.time(),
        )

    def recall(self, key: str) -> str | None:
        entry = self._store.get(key)
        if entry and not entry.forgotten:
            entry.last_accessed = time.time()
            return entry.value
        return None
```

Long-term memory is keyed — you store facts by topic ("voss_preferences", "reactor_history") and recall them when the context matches. Importance scores and access timestamps help prioritise what to include when the budget is tight.

---

## Memory decay

Not all memories are equal. A sensor reading from six months ago is less relevant than one from yesterday. **Decay** reduces memory importance over time:

```python
def tick_decay(self, decay_rate: float = 0.05):
    for entry in self._store.values():
        entry.importance *= (1.0 - decay_rate)
```

Call `tick_decay()` periodically (once per session, once per day — your choice). Entries below a threshold are effectively forgotten. This prevents the memory store from growing without bound and ensures recent information ranks higher in retrieval.

---

## The right to forget

Privacy matters even on a starship. When a crew member says "forget what I told you about my medical condition," the agent must comply.

```python
def forget(self, key: str):
    if key in self._store:
        self._store[key].forgotten = True
```

A `forgotten` flag is preferable to deletion — you maintain an audit trail that the data existed and was deliberately removed, without retaining the content.

---

## Summarisation

When a conversation grows long, you can replace old turns with a summary. The summary preserves the key facts and decisions while using far fewer tokens.

```python
def summarise_turns(turns: list[dict], max_tokens: int = 200) -> str:
    """Ask the LLM to compress turns into a single summary paragraph."""
    prompt = f"Summarise this conversation in one paragraph under {max_tokens} tokens:\n"
    for turn in turns:
        prompt += f"{turn['role']}: {turn['content']}\n"
    return llm.complete(prompt)
```

Replace the oldest N turns with a single system message containing the summary. The agent retains the gist of what was discussed without carrying every word.

---

## Field rules

- **Cap session memory.** Unbounded history overflows the context window and inflates costs.
- **Decay long-term memory.** Without decay, stale facts pollute retrieval.
- **Honour forget requests immediately.** Privacy is not optional.
- **Summarise before you truncate.** A summary beats silently dropping context.

---

## Demos

```bash
python module-07-agent-memory/demo/demo.py
```

All-in-one interactive walkthrough covering:
1. Session memory — capped buffer, FIFO eviction
2. Long-term memory — remember, recall, decay, forget
3. Summarisation — compress a long conversation
4. Memory-enhanced agent — chat with auto-memory detection

## Exercises

The three exercises chain together. Each builds on the last; you can bring your own code forward or use the provided solution.

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-memory-store`](exercises/01-memory-store/) | Build session + long-term memory with decay and forget, wire into a chat agent |
| [`exercises/02-conversation-summary`](exercises/02-conversation-summary/) | Auto-summarise long conversations to fit token budgets |
| [`exercises/03-memory-server`](exercises/03-memory-server/) | Expose memory as an MCP server, connect an agent via stdio |

Run tests for this module:

```bash
pytest module-07-agent-memory/
```

## Slides

From repo root: `pnpm slides:07`, or `cd module-07-agent-memory/slides && pnpm dev`.

## Reference

- [MemGPT (Packer et al. 2023)](https://arxiv.org/abs/2310.08560)
- [LangChain Memory](https://python.langchain.com/docs/concepts/memory/)
