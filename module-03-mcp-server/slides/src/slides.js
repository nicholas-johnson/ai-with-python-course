export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 4 — MCP Server',
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
        'Implement **practical tools**: crew lookup, sensor read, log search.',
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
      "name": "query_crew",
      "description": "Look up crew members",
      "inputSchema": {
        "type": "object",
        "properties": {
          "department": {"type": "string"}
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

server = FastMCP("Pathfinder Tools")

@server.tool()
def query_crew(department: str | None = None) -> str:
    """Look up crew members by department."""
    results = [m for m in crew if ...]
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
      title: 'Practical ship tools',
      icon: 'wrench',
      points: [
        '**read_sensor** — sensor telemetry by ID (simulated but deterministic).',
        '**query_crew** — crew manifest filtered by department.',
        '**search_logs** — keyword search over ship log entries.',
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
        'Not every officer should call every tool.',
        '**Scopes**: `crew:read`, `logs:read`, `weapons:fire` etc.',
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
      title: 'Field rules — Module 4',
      rules: [
        {
          rule: 'Schema is documentation',
          example: 'If the schema is wrong, the agent will call it wrong.',
          icon: 'file-text',
        },
        {
          rule: 'Auth before execution',
          example: 'Check scope first. No tool runs without clearance.',
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
      title: 'Exercises — Wiring the ship',
      points: [
        '01 — Hello MCP: your first tool server',
        '02 — Ship tools: sensor read, crew lookup, log search',
        '03 — Auth + observability: scopes and structured logs',
        '04 — MCP client: discover tools, validate args, call and handle errors',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Tools online — Module 4',
      subtitle: 'The ship has capabilities. Next: ground them with RAG.',
      icon: 'party-popper',
    },
  },
];
