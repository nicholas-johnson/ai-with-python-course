"""Part 5: Chat with the local weather server.

Requires OPENAI_API_KEY. The server is spawned over stdio — no extra terminal.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
WEATHER_SERVER_SCRIPT = str(Path(__file__).parent / "weather_server.py")


def log(tag: str, message: str):
    print(f"  [{tag}] {message}")


async def demo_weather_agent():
    print("=" * 60)
    print("PART 5: WEATHER AGENT")
    print("=" * 60)
    print()

    print("  A local stdio server with one tool: get_weather.")
    print("  The agent discovers it, then you chat. No URL, no weather API key.\n")

    server_params = StdioServerParameters(
        command=sys.executable, args=[WEATHER_SERVER_SCRIPT]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await _run_agent_loop(session)


async def _run_agent_loop(session: ClientSession):
    tools_raw = (await session.list_tools()).tools
    openai_tools = []

    for tool in tools_raw:
        openai_tools.append({
            "type": "function",
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        })
        summary = (tool.description or "").split("\n", 1)[0]
        log("discovery", f"  [weather/stdio]  {tool.name}: {summary}")

    log("discovery", f"\n  Total: {len(openai_tools)} tools from 1 server\n")

    client = OpenAI()
    messages = [
        {
            "role": "system",
            "content": (
                "You are a weather assistant for the DSS Pathfinder. "
                "Use get_weather to answer questions about current conditions "
                "and the short outlook. Be concise. Use fahrenheit only when "
                "the user asks for it."
            ),
        },
    ]

    print("  Chat with the weather agent. Type 'quit' to exit.")
    print("  Try: What's the weather in London?\n")

    while True:
        try:
            user_msg = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_msg or user_msg.lower() == "quit":
            break

        messages.append({"role": "user", "content": user_msg})
        log("user", user_msg)

        for _ in range(10):
            log("llm request", f"Sending {len(messages)} messages, {len(openai_tools)} tools")

            response = client.responses.create(
                model=MODEL, reasoning={"effort": "none"}, input=messages, tools=openai_tools
            )
            calls = [item for item in response.output if item.type == "function_call"]
            log("llm response", f"output items: {[item.type for item in response.output]}")

            if calls:
                log("llm response", f"  {len(calls)} tool call(s) requested")
                messages += response.output

                for tc in calls:
                    name = tc.name
                    args = json.loads(tc.arguments)
                    log("tool call", f"[weather/stdio] {name}({json.dumps(args)})")
                    tool_result = await session.call_tool(name, args)
                    text = tool_result.content[0].text if tool_result.content else ""
                    log("tool result", f"[weather/stdio] {text[:200]}")

                    messages.append({
                        "type": "function_call_output",
                        "call_id": tc.call_id,
                        "output": text,
                    })

            elif response.output_text:
                messages.append({"role": "assistant", "content": response.output_text})
                log("assistant", response.output_text)
                print()
                break
            else:
                log("assistant", "(no response)")
                print()
                break

    print("\n  Key points:")
    print("  - Same chat loop as Part 4, one server instead of two")
    print("  - stdio: this demo spawns weather_server.py for you")
    print("  - The model only knows get_weather because the server advertised it")
    print("  - The tool calls a live forecast. No weather API key")
