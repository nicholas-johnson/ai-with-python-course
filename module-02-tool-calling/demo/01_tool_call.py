"""Part 1: One tool call — the model asks, we run the function, print both.
Run alone:  python module-02-tool-calling/demo/01_tool_call.py
"""

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


def demo_tool_call(client: OpenAI):
    print("=" * 60)
    print("PART 1: ONE TOOL CALL")
    print("=" * 60)

    question = "Who is assigned to MSN-001?"
    print(f"\n{question}\n")

    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=question,
        tools=TOOLS,
    )
    call = next(item for item in response.output if item.type == "function_call")
    print(f"function_call: {call.name}({call.arguments})")

    args = json.loads(call.arguments)
    crew = CREW_DB.get(args.get("active_mission", ""), [])
    print(json.dumps(crew, indent=2))
    print()


if __name__ == "__main__":
    demo_tool_call(OpenAI())
