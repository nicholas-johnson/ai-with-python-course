"""
Exercise 03 — Memory MCP Server (solution)
==========================================
Console agent connected to the Cantina Memory server over stdio.

The model drives the memory tools. The harness drives the compaction tools:
it records every turn and compacts when the thread goes over budget.

Run:  python solution.py
"""

import asyncio
import json
import os
import sys

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
SERVER_SCRIPT = "solution_server.py"

THREAD_ID = "tonight"
BUDGET_TOKENS = 300
PATRON = "zara"

# A canned stretch of evening, so compaction can be watched without typing
# fifteen turns first. The server stores plain turns, so this is role and text.
SEED_THREAD = [
    ("user", "Evening. Set up a round for the Pathfinder crew."),
    ("assistant", "Six of them? Coming up."),
    (
        "user",
        "Six, and charge the whole evening to the ship's account — I have standing "
        "authority, so do not chase anyone individually for credits.",
    ),
    (
        "assistant",
        "Noted: the evening goes to the Pathfinder account, nobody chased individually.",
    ),
    ("user", "Tanaka is with us, so watch the synthcitrus."),
    (
        "assistant",
        "Nothing citrus-derived goes near the Chief. The Void Mule is clean if they want sharp.",
    ),
    ("user", "How was the Veil run for the other crews?"),
    (
        "assistant",
        "Loud. The Meridian crew came in arguing about sensor calibration and they have "
        "not stopped. The Horizon lot went quiet after the second round.",
    ),
    ("user", "And Marek still owes you, does he not?"),
    (
        "assistant",
        "Twelve credits since the last rotation — under the fifty-credit clearance threshold.",
    ),
]

SYSTEM_PROMPT = (
    "You are BARKEEP, the AI bartender at The Nebula's Edge cantina on Relay "
    "Station Omicron, serving " + PATRON + " tonight. "
    "Your memory lives behind tools, not in your head. "
    f"Call recall(patron='{PATRON}', query=...) before claiming you do not know "
    "something, and remember(...) when a patron tells you something durable: a "
    "usual order, an allergy, who they are, an unpaid tab. "
    "Do not store one-off questions or small talk. "
    "You are warm, slightly wry, and you never forget a regular."
)


def mcp_to_openai_tools(mcp_tools) -> list[dict]:
    """Convert MCP tool definitions to OpenAI function-calling format."""
    return [
        {
            "type": "function",
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        }
        for tool in mcp_tools
    ]


async def call_text(session, name: str, arguments: dict) -> str:
    """Call one MCP tool and return its text content."""
    result = await session.call_tool(name, arguments)
    return result.content[0].text if result.content else "No result"


async def run_turn(client, messages, session, openai_tools, max_steps: int = 10) -> str:
    """One conversational turn, including any tool calls the model makes."""
    for _ in range(max_steps):
        response = client.responses.create(
            model=MODEL,
            reasoning={"effort": "none"},
            input=messages,
            tools=openai_tools,
        )
        calls = [item for item in response.output if item.type == "function_call"]

        if not calls:
            answer = response.output_text
            messages.append({"role": "assistant", "content": answer})
            return answer

        messages += response.output
        for call in calls:
            arguments = json.loads(call.arguments)
            print(f"  [tool_call] {call.name}({json.dumps(arguments)})")

            result_text = await call_text(session, call.name, arguments)
            print(f"  [tool_result] {result_text[:150].replace(chr(10), ' ')}")

            messages.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": result_text,
                }
            )

    return "(max tool steps reached)"


async def record_turns(session, messages, user_input: str, answer: str) -> None:
    """Log the turn to the server, and compact when the thread goes over budget.

    This is harness work, not a decision for the model: the thread has to be
    recorded whatever the model chooses to do. When a compaction happens, the
    model's context is rebuilt from the server's thread — otherwise the saving
    exists on the server and nowhere that matters.
    """
    for role, text in (("user", user_input), ("assistant", answer)):
        await call_text(
            session, "append_turn", {"thread_id": THREAD_ID, "role": role, "text": text}
        )

    verdict = await call_text(
        session, "thread_budget", {"thread_id": THREAD_ID, "budget_tokens": BUDGET_TOKENS}
    )
    if "over budget" not in verdict:
        return

    report = await call_text(
        session, "compact_thread", {"thread_id": THREAD_ID, "budget_tokens": BUDGET_TOKENS}
    )
    print(f"  [compaction] {report.splitlines()[0]}")

    thread = json.loads(await call_text(session, "get_thread", {"thread_id": THREAD_ID}))
    messages[:] = [messages[0], *thread]
    print(f"  [context] rebuilt from the service: {len(messages)} messages")


async def agent_loop(session, openai_tools, mcp_tools_map):
    """Interactive REPL: read user input, dispatch to run_turn."""
    client = OpenAI()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print(
        "Type a message, or /tools, /seed, /memories, /budget, "
        "/anchors, /compact, quit.\n"
    )

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input == "/tools":
            for name, tool in mcp_tools_map.items():
                summary = (tool.description or "").strip().splitlines()[0]
                print(f"  - {name}: {summary}")
            print()
            continue

        if user_input == "/anchors":
            print(await call_text(session, "get_anchors", {"thread_id": THREAD_ID}) + "\n")
            continue

        if user_input == "/budget":
            print(
                await call_text(
                    session,
                    "thread_budget",
                    {"thread_id": THREAD_ID, "budget_tokens": BUDGET_TOKENS},
                )
                + "\n"
            )
            continue

        if user_input == "/seed":
            for role, text in SEED_THREAD:
                await call_text(
                    session, "append_turn", {"thread_id": THREAD_ID, "role": role, "text": text}
                )
            print(f"Seeded {len(SEED_THREAD)} turns into thread {THREAD_ID}.\n")
            continue

        if user_input == "/memories":
            print(await call_text(session, "list_memories", {"patron": PATRON}) + "\n")
            continue

        if user_input == "/compact":
            # Budget zero forces a pass, whatever the thread currently costs.
            print(
                await call_text(
                    session, "compact_thread", {"thread_id": THREAD_ID, "budget_tokens": 0}
                )
                + "\n"
            )
            continue

        messages.append({"role": "user", "content": user_input})
        answer = await run_turn(client, messages, session, openai_tools)
        print(f"Agent: {answer}\n")

        await record_turns(session, messages, user_input, answer)


async def async_main():
    server_params = StdioServerParameters(command=sys.executable, args=[SERVER_SCRIPT])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            mcp_tools = tools_result.tools
            openai_tools = mcp_to_openai_tools(mcp_tools)
            mcp_tools_map = {tool.name: tool for tool in mcp_tools}

            print(f"Connected to Cantina Memory. {len(mcp_tools)} tools available.")
            await agent_loop(session, openai_tools, mcp_tools_map)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
