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
    type: 'standard',
    content: {
      title: 'Passing tools to the model',
      icon: 'cpu',
      points: [
        'Tools are passed as a **`tools` parameter** alongside the messages in every API call.',
        'Each tool is a JSON object describing its **name**, **description**, and **parameter schema** — the model never sees your code, only this specification.',
        'The model reads the descriptions to decide **which tool to call** and what arguments to pass — good descriptions are critical.',
        'Tools are **not persistent** — you send the full list with every request, just like the message history.',
        'The model responds with a **`tool_calls` array** containing the tool name and arguments it chose, or with plain text if no tool is needed.',
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

  // ---- Demo: Tool registry  ----
  {
    type: 'title',
    content: {
      title: 'Demo — Tool registry',
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
        'LLMs are **unpredictable** — they can hallucinate tool names, loop indefinitely, or leak sensitive data.',
        'An unguarded agent is fine for demos. **Production requires boundaries.**',
        "Safety rails sit between the model's decision and the actual tool execution — a checkpoint layer.",
        'The model still sees denied calls as error messages, so it can **adapt and explain** rather than crash.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Allowlists',
      icon: 'shield',
      points: [
        '**What:** A set of permitted tool names. Any call to a tool not in the set is rejected before execution.',
        "**Why:** The model might hallucinate a tool name or try to call a destructive tool it shouldn't have access to.",
        '**Without it:** The agent can call *anything* — including tools you never intended to expose.',
        '**Example:** Permit `scan_planet` and `check_habitability`, block `log_discovery` — the agent can read but not write.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Rate limiting',
      icon: 'shield',
      points: [
        '**What:** Cap how many tool calls can happen within a sliding time window.',
        '**Why:** A confused or looping agent can fire hundreds of calls in seconds, burning through API budget and hammering downstream services.',
        '**Without it:** One bad prompt can trigger an infinite tool-call loop with no brake.',
        '**Pattern:** Track timestamps of recent calls, prune those outside the window, reject if the count exceeds the limit.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Redaction',
      icon: 'shield',
      points: [
        '**What:** Strip sensitive data — API keys, PII, credentials, internal IDs — from tool results before they reach logs or the model.',
        '**Why:** Tool results often contain raw data from internal systems. That data can end up in audit logs, conversation history, or even shown to the user.',
        '**Without it:** Secrets silently leak into stored conversations, log aggregators, or downstream models.',
        '**Pattern:** Regex or pattern-based replacement applied to every tool result before logging.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Audit logging',
      icon: 'shield',
      points: [
        '**What:** Record every tool call — allowed or blocked — with timestamp, tool name, arguments, result, and outcome.',
        '**Why:** When an agent misbehaves, the audit log is the only way to reconstruct what happened and why.',
        '**Without it:** No trail to debug incidents, measure usage, or prove compliance to stakeholders.',
        '**Each entry records:** was the call allowed? What arguments were passed? What came back? When did it happen?',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Blocked tool UX',
      icon: 'shield',
      points: [
        "**What:** When a tool is denied, return a structured error message as the tool result — don't crash or silently skip.",
        '**Why:** The model needs to *see* the denial so it can explain the situation to the user or try an alternative approach.',
        '**Without it:** The conversation breaks — the model expects a tool result and gets nothing, or the program crashes.',
        '**Example:** Return `{"error": "Tool not permitted: log_discovery"}` — the model reads this and says *"I can\'t log discoveries with my current permissions."*',
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
