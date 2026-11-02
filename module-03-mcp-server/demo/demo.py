"""
Module 3 Demo — MCP Server
Run:  python module-03-mcp-server/demo/demo.py

  Part 1: List the tools on the ship server
  Part 2: Explore the ship server (stdio)
  Part 3: Explore the navigation server (HTTP)
  Part 4: One agent, both servers
  Part 5: Chat with the weather and TV ratings servers

Requires:
  - OPENAI_API_KEY for Parts 4 and 5
  - http_server.py running for Parts 3 and 4:
      python module-03-mcp-server/demo/http_server.py
"""

import asyncio
from importlib import import_module

demo_list_tools = import_module("01_list_tools").demo_list_tools
demo_explore_stdio = import_module("02_stdio_server").demo_explore_stdio
demo_explore_http = import_module("03_http_server").demo_explore_http
demo_multi_server_agent = import_module("04_multi_server").demo_multi_server_agent
demo_weather_agent = import_module("05_weather_agent").demo_weather_agent

DEMOS = {
    "1": ("List tools (stdio)", demo_list_tools),
    "2": ("Explore ship server (stdio)", demo_explore_stdio),
    "3": ("Explore navigation server (HTTP)", demo_explore_http),
    "4": ("Multi-server LLM agent", demo_multi_server_agent),
    "5": ("Weather and TV agent (stdio)", demo_weather_agent),
}


async def main():
    print("\n" + "=" * 60)
    print("  MODULE 3 DEMO — MCP SERVER")
    print("=" * 60)

    while True:
        print("\nPick a section:\n")
        for key, (label, _) in DEMOS.items():
            print(f"  {key}. {label}")
        print("  q. Quit\n")

        try:
            choice = input("Enter choice> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice in ("q", "quit", ""):
            break
        elif choice in DEMOS:
            _, fn = DEMOS[choice]
            print()
            await fn()
        else:
            print(f"Unknown option: {choice}")

    print("\n" + "=" * 60)
    print("  RECAP")
    print("=" * 60)
    print()
    print("  1. list_tools       — connect, print the names, done")
    print("  2. stdio transport  — client spawns the server, no URL")
    print("  3. HTTP transport   — server at a URL, remote-friendly")
    print("  4. Multi-server     — one LLM, many MCP servers, mixed transports")
    print("  5. Live tools       — one LLM, weather and TV ratings, both over stdio")
    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
