"""Part 5: Chat with the local weather and TV ratings servers.

Requires OPENAI_API_KEY. Both servers are spawned over stdio — no extra terminal.
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
DEMO_DIR = Path(__file__).parent
WEATHER_SERVER_SCRIPT = str(DEMO_DIR / "weather_server.py")
TV_SERVER_SCRIPT = str(DEMO_DIR / "tv_server.py")


def log(tag: str, message: str):
    print(f"  [{tag}] {message}")


async def demo_weather_agent():
    print("=" * 60)
    print("PART 5: WEATHER AND TV AGENT")
    print("=" * 60)
    print()

    print("  Two local stdio servers: get_weather and get_show_rating.")
    print("  One agent discovers both, then you chat. No extra API keys.\n")

    weather_params = StdioServerParameters(command=sys.executable, args=[WEATHER_SERVER_SCRIPT])
    tv_params = StdioServerParameters(command=sys.executable, args=[TV_SERVER_SCRIPT])

    async with stdio_client(weather_params) as (weather_read, weather_write):
        async with ClientSession(weather_read, weather_write) as weather_session:
            await weather_session.initialize()

            async with stdio_client(tv_params) as (tv_read, tv_write):
                async with ClientSession(tv_read, tv_write) as tv_session:
                    await tv_session.initialize()
                    await _run_agent_loop(weather_session, tv_session)


async def _run_agent_loop(weather_session: ClientSession, tv_session: ClientSession):
    weather_tools = (await weather_session.list_tools()).tools
    tv_tools = (await tv_session.list_tools()).tools
    weather_names = {tool.name for tool in weather_tools}

    tool_router: dict[str, ClientSession] = {}
    openai_tools = []

    for tool in weather_tools:
        tool_router[tool.name] = weather_session
        openai_tools.append({
            "type": "function",
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        })
        summary = (tool.description or "").split("\n", 1)[0]
        log("discovery", f"  [weather/stdio]  {tool.name}: {summary}")

    for tool in tv_tools:
        tool_router[tool.name] = tv_session
        openai_tools.append({
            "type": "function",
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        })
        summary = (tool.description or "").split("\n", 1)[0]
        log("discovery", f"  [tv/stdio]       {tool.name}: {summary}")

    log("discovery", f"\n  Total: {len(openai_tools)} tools from 2 servers\n")

    client = OpenAI()
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant for the DSS Pathfinder crew. "
                "Use get_weather for current conditions and the short outlook. "
                "Use get_show_rating for TV show star ratings. Be concise. "
                "Use fahrenheit only when the user asks for it. "
                "Ratings are stars out of 5. If several shows match, name the "
                "one you used and mention the other titles."
            ),
        },
    ]

    print("  Chat with the agent. Type 'quit' to exit.")
    print("  Try: What's the weather in London?")
    print("       How many stars is The Office?\n")

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
                    session = tool_router[name]
                    source = "weather/stdio" if name in weather_names else "tv/stdio"

                    log("tool call", f"[{source}] {name}({json.dumps(args)})")
                    tool_result = await session.call_tool(name, args)
                    text = tool_result.content[0].text if tool_result.content else ""
                    log("tool result", f"[{source}] {text[:200]}")

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
    print("  - Same chat loop as Part 4, two stdio servers this time")
    print("  - Tool router maps each tool name to the right session")
    print("  - This demo spawns weather_server.py and tv_server.py for you")
    print("  - Both tools call live APIs. No weather or ratings API key")
