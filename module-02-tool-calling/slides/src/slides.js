export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 2 — Tool Calling',
      subtitle: 'The core pattern for AI agents',
      icon: 'cpu',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'An agent is a loop',
      points: [
        'Receive a message. Decide: think or act?',
        'If act: call a tool, feed the result back, loop.',
        'If think: produce a final answer. Done.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Understand the **message format** that drives agent conversations.',
        'Build a **tool-calling loop** from scratch.',
        'Implement a **tool registry** with validation and routing.',
        'Add **safety rails**: allowlists, rate limits, audit logs.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Message roles',
      icon: 'message-square',
      points: [
        '**system** — sets behaviour, available tools, constraints.',
        '**user** — the human (or upstream agent) input.',
        '**assistant** — the LLM response: text and/or tool calls.',
        '**tool** — result of a tool execution, linked by call_id.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Conversation state',
      code: `messages = [
    {"role": "system", "content": "You are a helpful assistant..."},
    {"role": "user", "content": "How many engineers are in the London office?"},
    {"role": "assistant", "tool_calls": [
        {"id": "c1", "name": "lookup_employees", "arguments": {...}}
    ]},
    {"role": "tool", "tool_call_id": "c1",
     "content": '[{"name": "Alice"}, ...]'},
    {"role": "assistant",
     "content": "3 engineers found: Alice, Bob, Carol."},
]`,
      highlights: [
        'The LLM decides whether to call a tool or answer directly',
        'Tool results come back as messages — the LLM interprets them',
      ],
    },
  },

  // ---- Demo: Tool-call message flow ----
  {
    type: 'title',
    content: {
      title: 'Demo — Tool-call message flow',
      subtitle: 'Switch to terminal: python demo/demo.py → Part 1',
      icon: 'rocket',
    },
  },

  // ---- Section: Tool calling loop ----
  {
    type: 'title',
    content: {
      title: 'The tool-calling loop',
      subtitle: 'From LLM decision to tool execution and back',
      icon: 'refresh-cw',
    },
  },

  {
    type: 'code',
    content: {
      title: 'The core loop',
      code: `def run_tool_loop(llm, tools, user_input, max_steps=10):
    messages = [system_msg, {"role": "user", "content": user_input}]

    for _ in range(max_steps):
        response = llm.chat(messages)

        if response.tool_calls:
            for tc in response.tool_calls:
                result = tools[tc.name](**tc.arguments)
                messages.append(...)  # assistant + tool messages
        elif response.content:
            return response.content  # final answer

    return None  # exhausted steps`,
      highlights: [
        'max_steps prevents infinite loops',
        'Each tool result is appended so the LLM sees the full context',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Tool registry pattern',
      icon: 'layers',
      points: [
        'Tools declare a **JSON schema**: name, description, parameters.',
        'Registry **validates** arguments before calling the handler.',
        'Registry **routes** by name and **catches** handler exceptions.',
        'OpenAI-compatible format: `{"type": "function", "function": {...}}`.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Registering a tool',
      code: `registry = ToolRegistry()

@registry.register(
    name="check_inventory",
    description="Check current inventory for a product",
    parameters={
        "type": "object",
        "properties": {
            "product": {"type": "string"}
        },
        "required": ["product"],
    },
)
def check_inventory(product: str) -> dict:
    return {"product": product, "stock": 42}`,
      highlights: [
        'Decorator pattern: schema lives next to the handler',
        'JSON schema doubles as documentation and validation spec',
      ],
    },
  },

  // ---- Demo: Tool registry (live agent) ----
  {
    type: 'title',
    content: {
      title: 'Demo — Tool registry (live agent)',
      subtitle: 'Switch to terminal: python demo/demo.py → Part 2',
      icon: 'rocket',
    },
  },

  // ---- Section: Safety rails ----
  {
    type: 'title',
    content: {
      title: 'Safety rails',
      subtitle: 'Allowlists, rate limits, and audit trails',
      icon: 'shield',
    },
  },

  {
    type: 'standard',
    content: {
      title: 'Why safety rails?',
      icon: 'shield',
      points: [
        'LLMs can hallucinate tool names or call tools in harmful sequences.',
        '**Allowlists**: only pre-approved tools can execute.',
        '**Rate limits**: prevent runaway loops or cost explosions.',
        '**Redaction**: strip sensitive data from logs and audit trails.',
        '**Audit log**: every call recorded for debugging and compliance.',
      ],
    },
  },
  {
    type: 'comparison',
    content: {
      title: 'Guarded vs unguarded execution',
      left: {
        label: 'Unguarded',
        items: [
          'Any tool name accepted',
          'No call frequency limits',
          'Secrets leak to logs',
          'No record of what happened',
        ],
      },
      right: {
        label: 'Guarded',
        items: [
          'Allowlist: only approved tools',
          'Rate limiter: N calls per window',
          'Redaction: sensitive data masked',
          'Audit trail: every call logged',
        ],
      },
    },
  },
  {
    type: 'code',
    content: {
      title: 'Rate limiter (sliding window)',
      code: `class RateLimiter:
    def __init__(self, max_calls: int, window: float):
        self.max_calls = max_calls
        self.window = window
        self._timestamps: list[float] = []

    def allow(self) -> bool:
        now = time.time()
        self._timestamps = [
            t for t in self._timestamps
            if now - t < self.window
        ]
        if len(self._timestamps) >= self.max_calls:
            return False
        self._timestamps.append(now)
        return True`,
      highlights: [
        'Sliding window: prune old timestamps, check count',
        'Simple, stateful, no external dependencies',
      ],
    },
  },

  // ---- Demo: Guarded agent ----
  {
    type: 'title',
    content: {
      title: 'Demo — Guarded agent',
      subtitle: 'Switch to terminal: python demo/demo.py → Part 3',
      icon: 'rocket',
    },
  },

  // ---- Section: Wrap-up ----
  {
    type: 'title',
    content: {
      title: 'Putting it all together',
      subtitle: 'Field rules and exercises',
      icon: 'lightbulb',
    },
  },

  {
    type: 'rules',
    content: {
      title: 'Field rules — Module 2',
      rules: [
        {
          rule: 'Always cap loop iterations',
          example: 'max_steps prevents runaway agents and surprise bills.',
          icon: 'shield',
        },
        {
          rule: 'Validate before you execute',
          example: 'Check allowlist + schema before calling any tool.',
          icon: 'check-square',
        },
        {
          rule: 'Log every tool call',
          example: 'An audit trail is your best debugging tool when agents misbehave.',
          icon: 'clipboard-list',
        },
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Exercises',
      subtitle: 'Time to build',
      icon: 'code',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Getting started',
      icon: 'settings',
      points: [
        'Activate your venv: **`source .venv/bin/activate`**.',
        'Each exercise has a **`start.py`** (your work) and **`test_start.py`** (pytest).',
        'Run tests with: **`pytest module-02-tool-calling/exercises/01-tool-calling-agent/`**.',
        'Solutions are in **`solution.py`** — try the exercise first!',
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises',
      points: [
        '01 — Tool-calling agent: the minimal LLM → tool → result cycle',
        '02 — Tool registry: schema, validation, routing',
        '03 — Guarded agent: allowlists, rate limits, and audit logs',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Module 2 — Complete',
      subtitle: 'Next: MCP and tool integration',
      icon: 'check-circle',
    },
  },
];
