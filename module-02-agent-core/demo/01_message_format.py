"""
Demo: Agent message format — make a real tool-calling API request and walk through the message trace.
Run:  python module-02-agent-core/demo/01_message_format.py

Requires: OPENAI_API_KEY environment variable.
"""

import json
from openai import OpenAI


TOOLS = [
    {
        "type": "function",
        "function": {
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
        mission = arguments.get("active_mission", "")
        crew = CREW_DB.get(mission, [])
        return json.dumps(crew)
    return json.dumps({"error": f"Unknown tool: {name}"})


def print_message(msg: dict, label: str = "") -> None:
    role = msg.get("role", "?").upper()
    header = f"[{role}]"
    if label:
        header += f" {label}"
    print(f"\n{header}")
    if msg.get("content"):
        print(f"  {msg['content']}")
    if msg.get("tool_calls"):
        for tc in msg["tool_calls"]:
            if hasattr(tc, "function"):
                print(f"  -> tool_call: {tc.function.name}({tc.function.arguments})")
            else:
                print(f"  -> tool_call: {tc}")
    if msg.get("tool_call_id"):
        print(f"  (responding to call_id={msg['tool_call_id']})")


if __name__ == "__main__":
    client = OpenAI()

    print("=== Agent Message Format — Live Demo ===")
    print("Sending a question that will trigger a tool call...\n")

    messages = [
        {"role": "system", "content": (
            "You are the DSS Pathfinder ship AI. You have access to a query_crew tool "
            "for looking up crew assigned to missions. Always cite the data source."
        )},
        {"role": "user", "content": "Who is assigned to mission MSN-001?"},
    ]

    for msg in messages:
        print_message(msg)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS,
    )
    assistant_msg = response.choices[0].message

    print_message({"role": "assistant", "tool_calls": assistant_msg.tool_calls})

    if assistant_msg.tool_calls:
        messages.append(assistant_msg)

        for tc in assistant_msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = execute_tool(tc.function.name, args)

            tool_msg = {
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            }
            messages.append(tool_msg)
            print_message(tool_msg, label=f"({tc.function.name})")

        final = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
        )
        final_msg = final.choices[0].message
        print_message({"role": "assistant", "content": final_msg.content})

    print("\n--- Key observations ---")
    print("1. System message sets the agent's behaviour and available tools.")
    print("2. Assistant can reply with content OR tool_calls (or both).")
    print("3. Tool results come back as role='tool' with the matching call_id.")
    print("4. The loop continues until the assistant replies with content only.")
