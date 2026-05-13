# Module 7 — Agent Memory + Workflows

> The Pathfinder AI handles hundreds of conversations a day — bridge crew asking about sensor data, engineering teams debugging reactor anomalies, science officers planning survey missions. Without memory, every conversation starts from scratch. This module gives the agent a memory system with short-term session recall and long-term profile storage, then builds structured workflows — ReAct and plan-and-execute — that let the agent reason methodically instead of guessing.

## Learning goals

- Distinguish **short-term** (session) and **long-term** (profile) memory.
- Implement **summarisation** to compress conversation history under token budgets.
- Model **memory decay** and explicit "do not remember" controls for privacy.
- Build a **ReAct loop** (Reason → Act → Observe).
- Compare ReAct with **plan-and-execute** workflows.

---

## Why agents need memory

An LLM has no memory between API calls. Every request is stateless — the model sees only the messages you send. "Memory" is a design pattern: you store information externally and inject it into the prompt when relevant.

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

## ReAct — Reason, Act, Observe

ReAct is a structured workflow where the agent explicitly reasons before acting. Each step has three phases:

1. **Thought** — the agent writes its reasoning (visible in logs, not shown to the user).
2. **Action** — the agent calls a tool.
3. **Observation** — the tool result is appended to the context.

The loop repeats until the agent's thought concludes with a final answer.

```python
def react_step(messages, tools) -> ReActStep:
    response = llm.chat(messages)  # generates Thought + Action
    thought = extract_thought(response)
    action = extract_action(response)

    if action.is_final:
        return ReActStep(thought=thought, answer=action.text)

    result = tools.call(action.tool, action.args)
    return ReActStep(thought=thought, action=action, observation=result)

def run_react(query, tools, max_steps=10):
    messages = [system_prompt, {"role": "user", "content": query}]
    trace = []
    for _ in range(max_steps):
        step = react_step(messages, tools)
        trace.append(step)
        if step.answer:
            return ReActResult(answer=step.answer, trace=trace)
        messages.append(...)  # append thought + observation
    return ReActResult(answer=None, trace=trace)
```

The trace is invaluable for debugging — you can see exactly why the agent made each decision. Log it in production.

---

## Plan-and-execute

ReAct decides one step at a time. Plan-and-execute takes a different approach: generate a complete plan first, then execute each step.

```
1. [Plan] Search logs for reactor anomalies
2. [Plan] Look up maintenance schedule
3. [Plan] Compare anomaly pattern to known failures
4. [Plan] Recommend action
```

The planner generates the full sequence. The executor runs each step, collecting results. If a step fails, the planner can revise the remaining steps.

| | ReAct | Plan-and-execute |
|-|-------|-----------------|
| Planning | One step at a time | Full plan up front |
| Adaptability | Highly reactive | Revises on failure |
| Traceability | Per-step thought logs | Full plan visible |
| Token cost | Lower per step | Higher for planning |
| Best for | Exploratory queries | Structured multi-step tasks |

---

## Field rules

- **Cap session memory.** Unbounded history overflows the context window and inflates costs.
- **Decay long-term memory.** Without decay, stale facts pollute retrieval.
- **Honour forget requests immediately.** Privacy is not optional.
- **Log the ReAct trace.** Thoughts + actions + observations are your best debugging tool.

---

## Demos

```bash
python module-07-agent-memory/demo/01_memory_types.py
python module-07-agent-memory/demo/02_summarisation.py
python module-07-agent-memory/demo/03_workflow_patterns.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-memory-store`](exercises/01-memory-store/) | Build session memory with caps and long-term memory with decay. |
| [`exercises/02-conversation-summary`](exercises/02-conversation-summary/) | Trim and summarise conversation history under a token budget. |
| [`exercises/03-react-loop`](exercises/03-react-loop/) | Implement a ReAct loop: thought → action → observation. |

Run tests for this module:

```bash
pytest module-07-agent-memory/
```

## Slides

From repo root: `pnpm slides:07`, or `cd module-07-agent-memory/slides && pnpm dev`.

## Reference

- [ReAct paper (Yao et al. 2023)](https://arxiv.org/abs/2210.03629)
- [Plan-and-Solve (Wang et al. 2023)](https://arxiv.org/abs/2305.04091)
- [LangGraph workflows](https://langchain-ai.github.io/langgraph/)
