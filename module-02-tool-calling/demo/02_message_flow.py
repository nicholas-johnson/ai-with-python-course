"""Part 2: Tool-call message flow — live chat, trace every item."""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

TOOLS = [
    {
        "type": "function",
        "name": "query_crew",
        "description": "Query crew members assigned to a mission.",
        "parameters": {
            "type": "object",
            "properties": {
                "active_mission": {"type": "string", "description": "Mission ID"},
            },
            "required": ["active_mission"],
        },
    },
]

CREW_DB = {
    "MSN-001": [
        {"id": "CRW-001", "name": "Commander Elara Voss"},
        {"id": "CRW-003", "name": "Chief Engineer Mira Chen"},
        {"id": "CRW-005", "name": "Ensign Dax Morel"},
        {"id": "CRW-011", "name": "Specialist Bodhi Kwan"},
    ],
}


def execute_tool(name: str, arguments: dict) -> str:
    if name == "query_crew":
        crew = CREW_DB.get(arguments.get("active_mission", ""), [])
        return json.dumps(crew)
    return json.dumps({"error": f"Unknown tool: {name}"})


def demo_message_format(client: OpenAI):
    print("=" * 60)
    print("PART 2: TOOL-CALL MESSAGE FLOW")
    print("=" * 60)
    print()
    print("  Chat with the Pathfinder AI. It has one tool: query_crew.")
    print("  Watch the flow: SYSTEM → USER → function_call → function_call_output → ASSISTANT")
    print("  Type 'quit' to return to the menu.\n")

    messages = [
        {
            "role": "system",
            "content": (
                "You are the DSS Pathfinder ship AI. You have access to a query_crew tool "
                "for looking up crew assigned to missions. Always cite the data source."
            ),
        },
    ]

    while True:
        try:
            user_msg = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_msg or user_msg.lower() == "quit":
            break

        messages.append({"role": "user", "content": user_msg})
        print(f"  [USER]      {user_msg}")

        response = client.responses.create(
            model=MODEL, reasoning={"effort": "none"}, input=messages, tools=TOOLS
        )
        calls = [item for item in response.output if item.type == "function_call"]

        if calls:
            messages += response.output
            for tc in calls:
                args = json.loads(tc.arguments)
                print(f"  [FUNCTION_CALL] {tc.name}({tc.arguments})")
                result = execute_tool(tc.name, args)
                print(f"  [TOOL]      {tc.name} returned: {result[:120]}")
                messages.append(
                    {"type": "function_call_output", "call_id": tc.call_id, "output": result}
                )

            final = client.responses.create(
                model=MODEL, reasoning={"effort": "none"}, input=messages, tools=TOOLS
            )
            answer = final.output_text
            messages.append({"role": "assistant", "content": answer})
            print(f"  [ASSISTANT] {answer}\n")
        else:
            content = response.output_text
            messages.append({"role": "assistant", "content": content})
            print(f"  [ASSISTANT] {content}\n")

    print("  Key concepts:")
    print("  • Messages (system, user, assistant) plus function_call / function_call_output items")
    print("  • The model decides whether to call a tool or answer directly")
    print("  • Tool results go back as function_call_output items — the model interprets them")
    print("  • This request-response loop is the foundation of every agent")
