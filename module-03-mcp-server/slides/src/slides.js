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
        'Build a **FastMCP server** with practical tools in Python.',
        'Build tools that access **live data**: web fetch, file I/O.',
        'Connect an MCP server to a **real agent** via stdio.',
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
        '**query_crew** — crew directory filtered by department or role.',
        '**search_logs** — keyword search over ship log entries.',
        '**read_sensor** — deterministic sensor readings by ID.',
        '**fetch_url** / **save_note** — tools with real-world side effects.',
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

  // ---- Demo: Connecting a client ----
  {
    type: 'title',
    content: {
      title: 'Demo — Connecting a client',
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
          rule: 'Handle errors gracefully',
          example: 'Return JSON errors, never crash. The agent needs to adapt.',
          icon: 'shield',
        },
        {
          rule: 'Sanitise all inputs',
          example: 'Filenames, URLs, queries — never trust user-controlled values.',
          icon: 'lock',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises',
      points: [
        '01 — MCP agent: build a FastMCP server and wire it to a console agent',
        '02 — Data tools: query crew, logs, sensors, and missions from JSON data',
        '03 — Live tools: fetch web pages and manage notes on disk',
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
