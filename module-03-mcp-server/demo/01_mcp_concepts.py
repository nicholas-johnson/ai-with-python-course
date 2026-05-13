"""
Demo: MCP concepts — tool discovery, schemas, and calling conventions.
Run:  python module-03-mcp-server/demo/01_mcp_concepts.py

This demo explains MCP structure without running a server — pure data walkthrough.
"""

import json


TOOL_DEFINITIONS = [
    {
        "name": "read_sensor",
        "description": "Read the latest value from a ship sensor by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sensor_id": {
                    "type": "string",
                    "description": "Sensor identifier (e.g. SEN-001)",
                },
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
                "department": {
                    "type": "string",
                    "description": "Department to filter by (optional)",
                },
            },
        },
    },
    {
        "name": "search_logs",
        "description": "Search ship logs by keyword or category.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term"},
                "category": {"type": "string", "description": "Log category filter"},
                "limit": {"type": "integer", "description": "Max results", "default": 5},
            },
            "required": ["query"],
        },
    },
]


EXAMPLE_CALL = {
    "method": "tools/call",
    "params": {
        "name": "read_sensor",
        "arguments": {"sensor_id": "SEN-007"},
    },
}

EXAMPLE_RESULT = {
    "content": [
        {
            "type": "text",
            "text": json.dumps({"sensor_id": "SEN-007", "value": 72.4, "unit": "celsius", "status": "nominal"}),
        }
    ],
}


if __name__ == "__main__":
    print("=== MCP Concepts ===\n")

    print("1. TOOL DISCOVERY — the server advertises what it can do:\n")
    for tool in TOOL_DEFINITIONS:
        required = tool["inputSchema"].get("required", [])
        params = list(tool["inputSchema"].get("properties", {}).keys())
        print(f"  {tool['name']}")
        print(f"    {tool['description']}")
        print(f"    params: {params}  required: {required}")
        print()

    print("2. TOOL CALL — the client (agent) sends a structured request:\n")
    print(f"  {json.dumps(EXAMPLE_CALL, indent=2)}\n")

    print("3. TOOL RESULT — the server returns structured content:\n")
    print(f"  {json.dumps(EXAMPLE_RESULT, indent=2)}\n")

    print("Key points:")
    print("  - MCP is a protocol, not a library — any language can implement it.")
    print("  - Tools declare JSON Schema for their inputs — agents validate before calling.")
    print("  - Results are 'content' arrays — text, images, or other media.")
    print("  - Discovery happens once; the agent caches the tool list.")
