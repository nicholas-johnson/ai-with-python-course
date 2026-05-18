"""
Module 3 Demo — MCP Server
Run:  python module-03-mcp-server/demo/demo.py

Walks through the full module in one script:
  Part 1: MCP concepts — tool discovery, schemas, calling conventions (data only)
  Part 2: Building a FastMCP server — decorator pattern, auto-generated schemas
  Part 3: Connecting a client — discover tools, convert to OpenAI format, call via agent

Part 3 spawns a real MCP server as a subprocess and connects to it.

Requires: OPENAI_API_KEY environment variable (Part 3 only).
"""

import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def pause():
    input("  [press Enter to continue]\n")


# ---------------------------------------------------------------------------
# Part 1: MCP Concepts — the protocol as data
# ---------------------------------------------------------------------------


def demo_mcp_concepts():
    section("Part 1: MCP Concepts — Protocol as Data")

    print("  MCP is JSON-RPC between an agent host and a tool server.")
    print("  Two key methods: tools/list (discovery) and tools/call (execution).\n")

    tool_definitions = [
        {
            "name": "read_sensor",
            "description": "Read the latest value from a ship sensor by ID.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sensor_id": {"type": "string", "description": "Sensor identifier"},
                },
                "required": ["sensor_id"],
            },
        },
        {
            "name": "query_crew",
            "description": "Look up crew members, optionally filtering by department.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "department": {"type": "string", "description": "Department filter (optional)"},
                },
            },
        },
        {
            "name": "search_logs",
            "description": "Search ship logs by keyword.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search term"},
                    "limit": {"type": "integer", "description": "Max results"},
                },
                "required": ["query"],
            },
        },
    ]

    print("  1. TOOL DISCOVERY — server advertises capabilities:\n")
    for tool in tool_definitions:
        required = tool["inputSchema"].get("required", [])
        params = list(tool["inputSchema"].get("properties", {}).keys())
        print(f"    {tool['name']}")
        print(f"      {tool['description']}")
        print(f"      params: {params}  required: {required}")
        print()

    print("  2. TOOL CALL — client sends a JSON-RPC request:\n")
    example_call = {
        "method": "tools/call",
        "params": {"name": "read_sensor", "arguments": {"sensor_id": "SEN-007"}},
    }
    print(f"    {json.dumps(example_call, indent=4)}\n")

    print("  3. TOOL RESULT — server returns structured content:\n")
    example_result = {
        "content": [{"type": "text", "text": '{"sensor_id": "SEN-007", "value": 72.4, "unit": "celsius"}'}]
    }
    print(f"    {json.dumps(example_result, indent=4)}\n")

    print("  Key points:")
    print("  • MCP is a protocol — any language can implement it")
    print("  • Tools declare JSON Schema for inputs — agents validate before calling")
    print("  • Results are 'content' arrays — text, images, or other media")
    print("  • Discovery happens once; the agent caches the tool list")


# ---------------------------------------------------------------------------
# Part 2: Building a FastMCP server — decorator pattern
# ---------------------------------------------------------------------------


def demo_fastmcp_server():
    section("Part 2: Building a FastMCP Server")

    print("  FastMCP generates schemas from type hints + docstrings.\n")

    print("  Code to define a server:\n")
    print("    from mcp.server.fastmcp import FastMCP")
    print("    mcp = FastMCP('Pathfinder')")
    print()
    print("    @mcp.tool()")
    print("    def greet(name: str) -> str:")
    print('        """Greet a crew member."""')
    print('        return f"Welcome aboard, {name}."')
    print()
    print("    @mcp.tool()")
    print("    def ship_status(system: str) -> str:")
    print('        """Check a ship system."""')
    print('        return f"{system}: online"')
    print()
    print("    mcp.run()  # starts stdio transport")
    print()

    print("  What this generates (tools/list response):\n")
    generated_schemas = [
        {
            "name": "greet",
            "description": "Greet a crew member.",
            "inputSchema": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
        {
            "name": "ship_status",
            "description": "Check a ship system.",
            "inputSchema": {
                "type": "object",
                "properties": {"system": {"type": "string"}},
                "required": ["system"],
            },
        },
    ]
    for schema in generated_schemas:
        print(f"    {json.dumps(schema, indent=4)}")
        print()

    print("  Key points:")
    print("  • Type hints -> JSON Schema (str -> 'string', int -> 'integer')")
    print("  • Docstrings become tool descriptions — keep them clear")
    print("  • mcp.run() handles JSON-RPC protocol over stdio")
    print("  • Add a new tool = add a decorated function. Agent discovers it automatically.")


# ---------------------------------------------------------------------------
# Part 3: Connecting a client — live agent demo
# ---------------------------------------------------------------------------


async def demo_mcp_client():
    section("Part 3: Connecting a Client — Live Agent")

    print("  The agent connects to the MCP server, discovers tools,")
    print("  converts them to OpenAI format, and uses them in a chat loop.\n")

    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    # The server script for this demo
    server_script = Path(__file__).parent / "_demo_server.py"

    if not server_script.exists():
        print("  (Creating a temporary demo server...)")
        server_script.write_text(
            'from mcp.server.fastmcp import FastMCP\n'
            'import json\n'
            '\n'
            'mcp = FastMCP("Demo Server")\n'
            '\n'
            '@mcp.tool()\n'
            'def get_crew_count(department: str) -> str:\n'
            '    """Count crew members in a department."""\n'
            '    counts = {"command": 1, "science": 3, "engineering": 2, "operations": 3}\n'
            '    count = counts.get(department, 0)\n'
            '    return json.dumps({"department": department, "count": count})\n'
            '\n'
            '@mcp.tool()\n'
            'def ship_status(system: str) -> str:\n'
            '    """Check the status of a ship system."""\n'
            '    systems = {"warp": "online (97%)", "shields": "online (85%)", "sensors": "degraded (62%)"}\n'
            '    return systems.get(system, f"{system}: unknown")\n'
            '\n'
            'if __name__ == "__main__":\n'
            '    mcp.run()\n'
        )

    print("  Step 1: Connect to MCP server via stdio...\n")

    server_params = StdioServerParameters(
        command=sys.executable, args=[str(server_script)]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.list_tools()
            tools = result.tools

            print(f"  Discovered {len(tools)} tools:")
            for tool in tools:
                print(f"    • {tool.name}: {tool.description}")

            print("\n  Step 2: Convert to OpenAI format...\n")

            openai_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema,
                    },
                }
                for tool in tools
            ]
            print(f"    {len(openai_tools)} tools ready for chat.completions.create()")

            print("\n  Step 3: Ask the LLM a question that triggers a tool call...\n")

            client = OpenAI()
            question = "How many crew are in the science department?"
            print(f"    Question: '{question}'\n")

            messages = [
                {"role": "system", "content": "You are a ship AI. Use tools to answer factual questions."},
                {"role": "user", "content": question},
            ]

            response = client.chat.completions.create(
                model=MODEL, messages=messages, tools=openai_tools
            )
            msg = response.choices[0].message

            if msg.tool_calls:
                tc = msg.tool_calls[0]
                print(f"    LLM requested: {tc.function.name}({tc.function.arguments})")

                args = json.loads(tc.function.arguments)
                tool_result = await session.call_tool(tc.function.name, args)
                result_text = tool_result.content[0].text if tool_result.content else ""
                print(f"    MCP returned:  {result_text}")

                messages.append(msg)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_text})

                final = client.chat.completions.create(
                    model=MODEL, messages=messages, tools=openai_tools
                )
                print(f"    Final answer:  {final.choices[0].message.content}")
            else:
                print(f"    Answer: {msg.content}")

    print("\n  Key points:")
    print("  • stdio_client spawns the server as a subprocess")
    print("  • list_tools() discovers capabilities dynamically")
    print("  • Convert MCP schemas to OpenAI format with a simple list comprehension")
    print("  • The agent loop: ask LLM -> call MCP tool -> feed result back -> repeat")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    demo_mcp_concepts()
    pause()

    demo_fastmcp_server()
    pause()

    asyncio.run(demo_mcp_client())

    print("\n" + "=" * 60)
    print("  Demo complete. Ready for exercises!")
    print("=" * 60)
