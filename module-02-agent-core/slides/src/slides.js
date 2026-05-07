export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 2 — Agent Core',
      subtitle: 'The tool-using loop that powers every AI on the Pathfinder',
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
        'Add **safety rails**: allowlists, rate limits, redaction.',
        'Write **golden-file tests** for deterministic evaluation.',
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
    {"role": "system", "content": "You are the Pathfinder AI..."},
    {"role": "user", "content": "Who is on the Kepler Sweep?"},
    {"role": "assistant", "tool_calls": [
        {"id": "c1", "name": "query_crew", "arguments": {...}}
    ]},
    {"role": "tool", "tool_call_id": "c1",
     "content": '[{"name": "Voss"}, ...]'},
    {"role": "assistant",
     "content": "4 crew assigned: Voss, Chen, Morel, Kwan."},
]`,
      highlights: [
        'The LLM decides whether to call a tool or answer directly',
        'Tool results come back as messages — the LLM interprets them',
      ],
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
    name="ship_status",
    description="Get current status of a ship system",
    parameters={
        "type": "object",
        "properties": {
            "system": {"type": "string"}
        },
        "required": ["system"],
    },
)
def ship_status(system: str) -> dict:
    return {"system": system, "status": "online"}`,
      highlights: [
        'Decorator pattern: schema lives next to the handler',
        'JSON schema doubles as documentation and validation spec',
      ],
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
  {
    type: 'standard',
    content: {
      title: 'Evaluation: golden-file testing',
      icon: 'check-square',
      points: [
        '**Golden case**: fixed input → expected tool calls + answer.',
        '**Mock LLM**: returns scripted responses (deterministic).',
        '**Replay**: same inputs always produce same outputs.',
        'Catches regressions when you change prompts or tool schemas.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Golden test structure',
      code: `case = GoldenCase(
    name="crew count query",
    user_input="How many in science?",
    expected_tool_names=["get_crew_count"],
    expected_answer_contains="3",
)

result = run_golden_test(case, agent_fn)
assert result.passed`,
      highlights: [
        'Declarative: describe what should happen, not how',
        'Easy to add new cases as you discover edge cases',
      ],
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
          rule: 'Test with mocks, not live LLMs',
          example: 'Golden tests are fast, deterministic, and free.',
          icon: 'flask',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises — Engineering the agent core',
      points: [
        '01 — Tool loop: the minimal LLM → tool → result cycle',
        '02 — Tool registry: schema, validation, routing',
        '03 — Safety + eval: rate limiting and golden-file tests',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Core online — Module 2',
      subtitle: 'The agent loop is running. Next: give it a voice.',
      icon: 'party-popper',
    },
  },
];
