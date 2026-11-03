"""
Module 6 Demo — 04: Graph agent
=================================
Spawn the knowledge-graph MCP server and let an agent choose the traversal.

The server is graph_server.py over stdio. This process discovers its tools
and runs an OpenAI tool loop. One scripted question shows the loop, then
you take over.

Run:  python module-06-structured-facts/demo/04_graph_agent.py

Requires: OPENAI_API_KEY. The graph server itself does not call a model.
"""

import asyncio
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
SERVER_SCRIPT = str(Path(__file__).resolve().parent / "graph_server.py")
MAX_ROUNDS = 8

SCRIPTED_QUESTION = "How is Mira Chen connected to the osmium found at Kepler-442?"
SUGGESTIONS = [
    "Who cleared EVA Team Alpha, and which shuttle was standing by?",
    "What happened to the warp core after Mira Chen's repair?",
    "Is the warp core connected to the Boötes Void?",
]

SYSTEM_PROMPT = (
    "You answer questions about Pathfinder missions using only the knowledge graph. "
    "Resolve uncertain names with list_entities. "
    "Use shortest_path when the question asks how two entities are connected. "
    "Use facts_about when the question asks what we know about one entity. "
    "Use neighbours for a single entity's immediate facts. "
    "Cite the source log id on every claim. "
    "If a fact's confidence is below 0.85, say that link is uncertain. "
    "If the tools report no path or no facts, say the graph does not contain it. "
    "Do not invent entities, relationships, or log ids."
)


def section(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def pause():
    input("  [press Enter to continue]\n")


def preview(text: str, limit: int = 400) -> str:
    flat = " ".join(text.split())
    if len(flat) <= limit:
        return flat
    return flat[:limit] + "…"


def show_tools(tools):
    for tool in tools:
        summary = (tool.description or "").split("\n", 1)[0]
        print(f"  {tool.name}")
        print(f"    {summary}")


def mcp_to_openai_tools(mcp_tools) -> list[dict]:
    return [
        {
            "type": "function",
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        }
        for tool in mcp_tools
    ]


async def run_turn(client, session, messages, openai_tools, user_text: str):
    """One user message: call the model until it stops requesting tools."""
    messages.append({"role": "user", "content": user_text})

    for round_index in range(1, MAX_ROUNDS + 1):
        response = client.responses.create(
            model=MODEL,
            reasoning={"effort": "none"},
            input=messages,
            tools=openai_tools,
        )
        calls = [item for item in response.output if item.type == "function_call"]

        if not calls:
            answer = response.output_text or "(no response)"
            messages.append({"role": "assistant", "content": answer})
            print(f"\n  Agent: {answer}\n")
            return

        print(f"\n  Round {round_index}: {len(calls)} tool call(s)")
        messages += response.output

        for call in calls:
            name = call.name
            args = json.loads(call.arguments)
            print(f"  → {name}({json.dumps(args, ensure_ascii=False)})")
            result = await session.call_tool(name, args)
            text = result.content[0].text if result.content else ""
            print(f"    ← {preview(text)}")
            messages.append({
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": text,
            })

    print(f"\n  Stopped after {MAX_ROUNDS} tool rounds.\n")


async def async_main():
    section("Part 1: The graph is a server")

    print("  graph_server.py loads graph.json into networkx and exposes four tools.")
    print("  This demo spawns it over stdio. The server does not call a model.")
    print("  Same names as the extraction schema: subject, predicate, object,")
    print("  confidence, and the source sentence — one canonical name per entity.\n")
    print("  Connecting...\n")

    params = StdioServerParameters(command=sys.executable, args=[SERVER_SCRIPT])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            openai_tools = mcp_to_openai_tools(tools)

            print(f"  Discovered {len(tools)} tools:\n")
            show_tools(tools)

            print("\n  A direct call, before any model is involved.")
            print('  shortest_path(start="Mira Chen", end="Warp core")\n')
            direct = await session.call_tool(
                "shortest_path", {"start": "Mira Chen", "end": "Warp core"}
            )
            direct_text = direct.content[0].text if direct.content else ""
            print(json.dumps(json.loads(direct_text), indent=2, ensure_ascii=False))

            pause()

            section("Part 2: The agent chooses the tools")

            print("  Same server. Now the model decides which tool to call.")
            print("  Watch the rounds: resolve a name, walk, then answer from the facts.\n")
            print(f"  You: {SCRIPTED_QUESTION}")

            client = OpenAI()
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            await run_turn(client, session, messages, openai_tools, SCRIPTED_QUESTION)

            pause()

            section("Part 3: Ask the graph (interactive)")

            print("  The conversation keeps its tool results, so follow-ups work.")
            print("  /tools lists the server tools. quit exits.\n")
            print("  Try:")
            for suggestion in SUGGESTIONS:
                print(f"    {suggestion}")
            print()

            while True:
                try:
                    user_text = input("  You: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if not user_text:
                    continue
                if user_text.lower() == "quit":
                    break
                if user_text == "/tools":
                    print()
                    show_tools(tools)
                    print()
                    continue

                await run_turn(client, session, messages, openai_tools, user_text)

    print("  Demo complete!")
    print("  The graph never saw the model. The model never saw the edges,")
    print("  except through the tools it chose to call.")


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
