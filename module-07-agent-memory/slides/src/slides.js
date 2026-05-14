export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 7 — Agent Memory',
      subtitle: 'What to remember, what to forget, and how to keep it all in context',
      icon: 'brain',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'The ship remembers',
      points: [
        'Useful agents need session context, durable preferences, and policies for forgetting.',
        'Short-term vs long-term memory — different stores, different lifetimes.',
        'Summarisation compresses old conversations to fit the context window.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Implement **short-term memory** (session buffer) separate from **long-term** storage.',
        'Apply **summarisation** to fit context limits gracefully.',
        'Model **decay** and explicit **"do not remember"** controls.',
        'Expose memory as **MCP tools** for any agent to use.',
      ],
    },
  },
  {
    type: 'comparison',
    content: {
      title: 'Short-term vs long-term memory',
      left: {
        label: 'Short-term (session)',
        items: [
          'Current conversation turns',
          'Lives in RAM or session store',
          'Cleared on session end',
          'Capped by token budget',
        ],
      },
      right: {
        label: 'Long-term (profile)',
        items: [
          'User preferences, notes, facts',
          'Persisted to disk / database',
          'Survives across sessions',
          'Subject to decay and privacy rules',
        ],
      },
    },
  },
  {
    type: 'code',
    content: {
      title: 'Session memory with cap',
      code: `class SessionMemory:
    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self._turns: list[dict] = []

    def add(self, message: dict):
        self._turns.append(message)
        while len(self._turns) > self.max_turns:
            self._turns.pop(0)  # drop oldest

    def get_messages(self) -> list[dict]:
        return list(self._turns)

    def clear(self):
        self._turns.clear()`,
      highlights: [
        'FIFO eviction: oldest turns drop when the buffer is full',
        'Simple but effective — production systems add summarisation',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Long-term memory with decay',
      code: `class LongTermMemory:
    def __init__(self, decay_rate: float = 0.05):
        self._entries: dict[str, dict] = {}
        self.decay_rate = decay_rate

    def remember(self, key: str, value: str, importance: float = 1.0):
        self._entries[key] = {
            "value": value, "importance": importance
        }

    def tick_decay(self):
        expired = []
        for key, entry in self._entries.items():
            entry["importance"] -= self.decay_rate
            if entry["importance"] <= 0:
                expired.append(key)
        for key in expired:
            del self._entries[key]`,
      highlights: [
        'Importance decays over time — unused facts eventually disappear',
        'remember() can refresh importance when a fact is referenced again',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Summarisation — fitting context',
      icon: 'file-minus',
      points: [
        'When the conversation exceeds the budget, **summarise** older turns.',
        'Replace 20 old messages with one **summary paragraph**.',
        'Keep the system prompt + summary + recent N turns.',
        'Trade-off: detail vs budget. Summaries lose nuance.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Summarise and trim',
      code: `def summarise_and_trim(messages, llm, max_tokens):
    total = count_tokens(messages)
    if total <= max_tokens:
        return messages

    # Split: system + old turns + recent turns
    system = messages[0]
    split = len(messages) // 2
    old_turns = messages[1:split]
    recent = messages[split:]

    summary = llm.chat([
        {"role": "system", "content": "Summarise this conversation."},
        *old_turns,
    ])

    return [system, {"role": "system", "content":
        f"Earlier conversation summary: {summary}"
    }, *recent]`,
      highlights: [
        'The LLM itself produces the summary — meta but effective',
        'Recent turns stay verbatim for conversational continuity',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Privacy: "do not remember"',
      icon: 'eye-off',
      points: [
        'Users may request deletion: **"forget my medical data"**.',
        'Implement a **forget(key)** method that removes from all stores.',
        'Long-term memory entries can have a **do_not_persist** flag.',
        'Audit log: record *that* something was forgotten, not *what*.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Memory as MCP tools',
      icon: 'wrench',
      points: [
        'Wrap memory behind a **FastMCP server** with remember/recall/forget tools.',
        'Any agent can connect via stdio and use memory without importing code.',
        'Memory persists as long as the server runs — agents can restart.',
        'This is how production systems separate concerns: memory is a service.',
      ],
    },
  },
  {
    type: 'rules',
    content: {
      title: 'Field rules — Module 7',
      rules: [
        {
          rule: 'Separate session from profile',
          example: 'Session clears on logout; profile persists across visits.',
          icon: 'database',
        },
        {
          rule: 'Summarise before you truncate',
          example: 'A summary beats silently dropping context.',
          icon: 'file-minus',
        },
        {
          rule: 'Honour forget requests immediately',
          example: 'Privacy is not optional — flag and stop serving.',
          icon: 'eye-off',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises — Teaching the ship to remember',
      points: [
        '01 — Memory store: session buffer + long-term memory with decay and forget',
        '02 — Conversation summary: auto-summarise when the buffer overflows',
        '03 — Memory MCP server: expose memory as tools, connect an agent via stdio',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Memory banks online — Module 7',
      subtitle: 'The ship remembers. Next: structured workflows.',
      icon: 'party-popper',
    },
  },
];
