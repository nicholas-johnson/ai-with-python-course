export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 3 — MCP Server',
      subtitle: 'Capabilities as tools: the standard protocol for AI agents',
      icon: 'server',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'One protocol to connect them all',
      points: [
        'MCP lets any AI agent discover and call tools uniformly.',
        'No custom glue per integration — just schemas and conventions.',
        'Build once, connect to any MCP-compatible agent or IDE.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Understand **MCP concepts**: discovery, schemas, calling conventions.',
        'Build a **minimal MCP server** in Python.',
        'Implement **practical tools**: user lookup, metrics read, log search.',
        'Add **auth scopes** and **structured logging**.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'What is MCP?',
      icon: 'globe',
      points: [
        '**Model Context Protocol** — an open standard for tool integration.',
        'Server advertises tools with JSON Schema inputs.',
        'Client (agent) discovers tools, validates args, calls them.',
        'Transport: stdio, HTTP/SSE, or WebSocket.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Tool discovery response',
      code: `{
  "tools": [
    {
      "name": "lookup_users",
      "description": "Look up users by role",
      "inputSchema": {
        "type": "object",
        "properties": {
          "role": {"type": "string"}
        }
      }
    }
  ]
}`,
      highlights: [
        'JSON Schema describes what each tool accepts',
        'Agents use this to validate before calling',
      ],
    },
  },
  // ---- Demo: MCP concepts ----
  {
    type: 'title',
    content: {
      title: 'Demo — MCP concepts',
      subtitle: 'Switch to terminal: python demo/demo.py — Part 1',
      icon: 'rocket',
    },
  },

  // ---- Section: Building an MCP server ----
  {
    type: 'title',
    content: {
      title: 'Building an MCP server',
      subtitle: 'FastMCP: decorators, schemas, and transports',
      icon: 'server',
    },
  },

  {
    type: 'code',
    content: {
      title: 'Building an MCP server with FastMCP',
      code: `from mcp.server.fastmcp import FastMCP

server = FastMCP("API Tools")

@server.tool()
def lookup_users(role: str | None = None) -> str:
    """Look up users by role."""
    results = [m for m in users if ...]
    return json.dumps(results)

server.run()  # stdio transport`,
      highlights: [
        'FastMCP generates schemas from type hints + docstrings',
        'server.run() starts the stdio transport loop',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Practical tools',
      icon: 'wrench',
      points: [
        '**read_metrics** — system metrics by ID (simulated but deterministic).',
        '**lookup_users** — user directory filtered by role.',
        '**search_logs** — keyword search over application log entries.',
        'All read from shared JSON data files — no side effects.',
      ],
    },
  },
  // ---- Demo: FastMCP server ----
  {
    type: 'title',
    content: {
      title: 'Demo — FastMCP server',
      subtitle: 'Switch to terminal: python demo/demo.py — Part 2',
      icon: 'rocket',
    },
  },

  // ---- Section: Auth + observability ----
  {
    type: 'title',
    content: {
      title: 'Auth + observability',
      subtitle: 'Scopes, structured logs, and audit trails',
      icon: 'lock',
    },
  },

  {
    type: 'standard',
    content: {
      title: 'Auth + permissions model',
      icon: 'lock',
      points: [
        'Not every client should call every tool.',
        '**Scopes**: `users:read`, `logs:read`, `admin:write` etc.',
        '**AuthContext**: user_id + role + scopes.',
        'Check scope before every tool call — deny early, log always.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Scoped tool execution',
      code: `class AuthenticatedToolRunner:
    def call(self, tool, args, auth: AuthContext):
        required = self._scopes[tool]
        if required not in auth.scopes:
            self._log(auth.user_id, tool, False)
            return {"error": "Access denied"}
        result = self._handlers[tool](**args)
        self._log(auth.user_id, tool, True)
        return {"result": result}`,
      highlights: [
        'Scope check before execution, never after',
        'Every call logged regardless of outcome',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Structured logging for observability',
      icon: 'clipboard-list',
      points: [
        'Every tool call produces a structured log entry.',
        'Fields: timestamp, user_id, tool, arguments, allowed, result_preview.',
        'Enables dashboards, alerts, and compliance audits.',
        'Preview is truncated — never log full secrets or large payloads.',
      ],
    },
  },
  // ---- Demo: MCP client ----
  {
    type: 'title',
    content: {
      title: 'Demo — MCP client',
      subtitle: 'Switch to terminal: python demo/demo.py — Part 3',
      icon: 'rocket',
    },
  },

  // ---- Section: Wrap-up ----
  {
    type: 'title',
    content: {
      title: 'Putting it all together',
      subtitle: 'Field rules and exercises',
      icon: 'check-square',
    },
  },

  {
    type: 'rules',
    content: {
      title: 'Field rules — Module 3',
      rules: [
        {
          rule: 'Schema is documentation',
          example: 'If the schema is wrong, the agent will call it wrong.',
          icon: 'file-text',
        },
        {
          rule: 'Auth before execution',
          example: 'Check scope first. No tool runs without authorisation.',
          icon: 'lock',
        },
        {
          rule: 'Log everything, redact secrets',
          example: 'Ops needs the trail; they do not need the passwords.',
          icon: 'clipboard-list',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises',
      points: [
        '01 — Hello MCP: your first tool server',
        '02 — Practical tools: metrics, user lookup, log search',
        '03 — Auth + observability: scopes and structured logs',
        '04 — MCP client: discover tools, validate args, call and handle errors',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Module 3 — Complete',
      subtitle: 'Next: GenAI strategies',
      icon: 'check-circle',
    },
  },
];
