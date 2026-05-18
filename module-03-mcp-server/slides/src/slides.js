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
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Understand **MCP concepts**: discovery, schemas, calling conventions.',
        'Build a **FastMCP server** with practical tools in Python.',
        'Compare **transports**: stdio (local) vs Streamable HTTP (remote).',
        'Connect **multiple MCP servers** to a single LLM agent.',
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
        'Same protocol, multiple transports — choose the right one for your use case.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Two ways to connect to an MCP server',
      icon: 'radio',
      points: [
        '**Local stdio** — the client **spawns** the server as a child process and pipes JSON-RPC over stdin/stdout. No port, no URL — the client starts and stops the server automatically. This is how **Cursor** and **Claude Desktop** work.',
        '**Remote HTTP** — the server runs independently at a URL (e.g. `localhost:8000/mcp`). You start it yourself. For **shared team servers**, cloud deployment, cross-network access.',
        'Same JSON-RPC protocol, same tool schemas — different wire format.',
        'One-line change: `server.run()` vs `server.run(transport="streamable-http")`.',
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

  // ---- Section: Building an MCP server ----
  {
    type: 'title',
    content: {
      title: 'Building a local MCP server',
      subtitle: 'FastMCP: decorators, schemas, and transports',
      icon: 'server',
    },
  },

  {
    type: 'code',
    content: {
      title: 'Building a local MCP server with FastMCP',
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
        'server.run() listens on stdin — the client spawns and manages this process',
      ],
    },
  },

  // ---- Demo Part 1: Ship server (stdio) ----
  {
    type: 'title',
    content: {
      title: 'Demo — Explore ship server (stdio)',
      subtitle: 'Switch to terminal: python demo/demo.py',
      icon: 'rocket',
    },
  },

  // ---- Section: Remote MCP server ----
  {
    type: 'title',
    content: {
      title: 'Exploring a remote MCP server',
      subtitle: 'Streamable HTTP: the same protocol over a URL',
      icon: 'wifi',
    },
  },

  {
    type: 'standard',
    content: {
      title: 'Streamable HTTP transport',
      icon: 'radio',
      points: [
        'Server runs independently at a URL — like any web service.',
        'Same JSON-RPC protocol, same tool schemas — just a different wire format.',
        'Use **streamablehttp_client** to connect from Python.',
        'Ideal for **shared team servers**, cloud deployment, cross-network access.',
        'The server doesn\'t need to be rewritten — one-line change to the transport.',
      ],
    },
  },

  // ---- Demo Part 2: Navigation server (HTTP) ----
  {
    type: 'title',
    content: {
      title: 'Demo — Explore navigation server (HTTP)',
      subtitle: 'Switch to terminal: python demo/demo.py (first run python http_server.py in a separate terminal)',
      icon: 'rocket',
    },
  },

  // ---- Section: Connecting an LLM to MCP ----
  {
    type: 'title',
    content: {
      title: 'Connecting an LLM to MCP',
      subtitle: 'From tool discovery to agent loop',
      icon: 'cpu',
    },
  },

  {
    type: 'standard',
    content: {
      title: 'Wiring MCP servers to an LLM',
      icon: 'link',
      points: [
        '**Discover** tools from each server with `session.list_tools()` — merge them into one list.',
        '**Convert** MCP schemas to the OpenAI `tools` parameter format.',
        '**Route** calls: build a map of `tool_name → session` so you know which server to call.',
        'When the LLM requests a tool call, **look up** the right session and call `session.call_tool(name, args)`.',
        'The LLM doesn\'t know or care which server a tool lives on — routing is your agent\'s job.',
      ],
    },
  },

  // ---- Demo Part 3: Multi-server LLM agent ----
  {
    type: 'title',
    content: {
      title: 'Demo — Multi-server LLM agent',
      subtitle: 'Switch to terminal: python demo/demo.py (http_server.py still running)',
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
