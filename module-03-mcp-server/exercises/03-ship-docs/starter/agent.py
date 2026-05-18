"""
Exercise 03 — Multi-server MCP Agent with Resources (provided)
Connects to 3 servers: local_server.py (stdio), http_server.py (HTTP), server.py (stdio).
Reads MCP resources from the docs server to provide context to the LLM.
"""

import asyncio
import json
import sys
from pathlib import Path

import openai
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

SYSTEM_PROMPT = (
    "You are the station AI. You have access to power grid tools, science lab tools, "
    "and ship documentation. Use your tools to answer queries. When asked about "
    "procedures or protocols, search the ship docs first. Be concise."
)

LOCAL_SERVER = str(Path(__file__).parent / "local_server.py")
DOCS_SERVER = str(Path(__file__).parent / "server.py")
HTTP_SERVER_URL = "http://localhost:8000/mcp"


async def run_agent(tool_router, openai_tools, resource_context):
    client = openai.OpenAI()
    system_content = SYSTEM_PROMPT
    if resource_context:
        system_content += "\n\nShip documentation index:\n" + resource_context

    messages = [{"role": "system", "content": system_content}]

    print("Station AI ready (power + lab + docs). Type a question (or 'quit').\n")

    while True:
        try:
            user_input = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input or user_input.lower() in ("quit", "exit"):
            break

        messages.append({"role": "user", "content": user_input})

        for _ in range(10):
            response = client.chat.completions.create(
                model="gpt-4o-mini", messages=messages, tools=openai_tools
            )
            msg = response.choices[0].message

            if msg.tool_calls:
                messages.append(msg)
                for tc in msg.tool_calls:
                    name = tc.function.name
                    args = json.loads(tc.function.arguments)
                    session = tool_router[name]
                    print(f"  [tool] {name}({json.dumps(args)})")
                    result = await session.call_tool(name, arguments=args)
                    text = result.content[0].text if result.content else ""
                    print(f"  [result] {text[:120]}")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": text,
                    })
            elif msg.content:
                messages.append({"role": "assistant", "content": msg.content})
                print(f"AI> {msg.content}\n")
                break
            else:
                print("AI> (no response)\n")
                break


async def main():
    power_params = StdioServerParameters(command=sys.executable, args=[LOCAL_SERVER])
    docs_params = StdioServerParameters(command=sys.executable, args=[DOCS_SERVER])

    async with stdio_client(power_params) as (p_read, p_write):
        async with ClientSession(p_read, p_write) as power_session:
            await power_session.initialize()

            async with streamablehttp_client(HTTP_SERVER_URL) as (h_read, h_write, _):
                async with ClientSession(h_read, h_write) as lab_session:
                    await lab_session.initialize()

                    async with stdio_client(docs_params) as (d_read, d_write):
                        async with ClientSession(d_read, d_write) as docs_session:
                            await docs_session.initialize()

                            tool_router = {}
                            openai_tools = []

                            sessions = [
                                ("power", power_session),
                                ("lab", lab_session),
                                ("docs", docs_session),
                            ]

                            for label, session in sessions:
                                for tool in (await session.list_tools()).tools:
                                    tool_router[tool.name] = session
                                    openai_tools.append({
                                        "type": "function",
                                        "function": {
                                            "name": tool.name,
                                            "description": tool.description or "",
                                            "parameters": tool.inputSchema,
                                        },
                                    })

                            # Read resources from the docs server
                            resource_context = ""
                            resources = (await docs_session.list_resources()).resources
                            if resources:
                                print(f"  [resources] Found {len(resources)} resources from docs server")
                                for r in resources:
                                    if str(r.uri) == "docs://index":
                                        content = await docs_session.read_resource(r.uri)
                                        if content.contents:
                                            resource_context = content.contents[0].text
                                        break

                            print(f"Connected to 3 servers. {len(openai_tools)} tools, {len(resources)} resources.")
                            for t in openai_tools:
                                print(f"  - {t['function']['name']}: {t['function']['description']}")
                            print()

                            await run_agent(tool_router, openai_tools, resource_context)


if __name__ == "__main__":
    asyncio.run(main())
