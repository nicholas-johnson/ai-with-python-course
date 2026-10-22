"""
Exercise 01 — Golden Tests (Solution)

Regression-test a tool-calling agent with a mock LLM.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

TOOLS: list[dict] = [
    {
        "type": "function",
        "name": "get_crew_count",
        "description": "Count crew in a department.",
        "parameters": {
            "type": "object",
            "properties": {"department": {"type": "string"}},
            "required": ["department"],
        },
    },
    {
        "type": "function",
        "name": "get_ship_status",
        "description": "Status of a ship system (warp, shields, sensors, life_support).",
        "parameters": {
            "type": "object",
            "properties": {"system": {"type": "string"}},
            "required": ["system"],
        },
    },
    {
        "type": "function",
        "name": "search_crew",
        "description": "Search crew by name or role.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
]

CREW_DATA = {
    "command": [{"name": "Commander Elara Voss", "role": "Captain"}],
    "science": [
        {"name": "Dr. Jian Chen", "role": "Chief Science Officer"},
        {"name": "Ensign Dax Morel", "role": "Xenobiologist"},
    ],
    "engineering": [
        {"name": "Chief Engineer Mira Chen", "role": "Lead Engineer"},
        {"name": "Specialist Bodhi Kwan", "role": "Systems Tech"},
    ],
    "medical": [{"name": "Dr. Amara Osei", "role": "Chief Medical Officer"}],
}

SHIP_SYSTEMS = {
    "warp": {"system": "warp", "status": "online", "efficiency": 0.97},
    "shields": {"system": "shields", "status": "online", "efficiency": 0.85},
    "sensors": {"system": "sensors", "status": "degraded", "efficiency": 0.62},
    "life_support": {"system": "life_support", "status": "online", "efficiency": 0.99},
}


def get_crew_count(department: str) -> str:
    crew = CREW_DATA.get(department, [])
    return json.dumps({"department": department, "count": len(crew)})


def get_ship_status(system: str) -> str:
    data = SHIP_SYSTEMS.get(system)
    if data is None:
        return json.dumps({"error": f"Unknown system: {system}"})
    return json.dumps(data)


def search_crew(query: str) -> str:
    needle = query.lower()
    hits = [
        member
        for members in CREW_DATA.values()
        for member in members
        if needle in member["name"].lower() or needle in member["role"].lower()
    ]
    return json.dumps(hits)


HANDLERS = {
    "get_crew_count": get_crew_count,
    "get_ship_status": get_ship_status,
    "search_crew": search_crew,
}

SYSTEM_PROMPT = (
    "You are the DSS Pathfinder ship AI. Use tools for crew and system queries. Be concise."
)


def make_scripted_client(scripted_responses: list[dict]):
    queue = list(scripted_responses)

    def _to_response(item: dict):
        if "tool_calls" in item:
            calls = []
            for i, tc in enumerate(item["tool_calls"]):
                args = tc["arguments"]
                if not isinstance(args, str):
                    args = json.dumps(args)
                calls.append(
                    SimpleNamespace(
                        type="function_call",
                        call_id=tc.get("id", f"call_{i}"),
                        name=tc["name"],
                        arguments=args,
                    )
                )
            return SimpleNamespace(output=calls, output_text="")
        return SimpleNamespace(output=[], output_text=item.get("content", ""))

    def create(**kwargs):
        if not queue:
            raise RuntimeError("Scripted client has no more responses")
        return _to_response(queue.pop(0))

    return SimpleNamespace(responses=SimpleNamespace(create=create))


def run_case(client, case: dict, max_steps: int = 5) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": case["question"]},
    ]
    tools_used: list[dict] = []
    answer = None

    for _ in range(max_steps):
        response = client.responses.create(
            model=MODEL,
            reasoning={"effort": "none"},
            input=messages,
            tools=TOOLS,
        )
        calls = [item for item in response.output if item.type == "function_call"]
        if calls:
            messages += response.output
            for tc in calls:
                name = tc.name
                arguments = json.loads(tc.arguments)
                tools_used.append({"name": name, "arguments": arguments})
                handler = HANDLERS.get(name)
                if handler is None:
                    result = json.dumps({"error": f"Unknown tool: {name}"})
                else:
                    result = handler(**arguments)
                messages.append(
                    {
                        "type": "function_call_output",
                        "call_id": tc.call_id,
                        "output": result,
                    }
                )
        elif response.output_text:
            answer = response.output_text
            break

    return {"tools": tools_used, "answer": answer}


def score_case(result: dict, case: dict) -> dict:
    mismatches: list[str] = []
    if result.get("tools") != case["expected_tools"]:
        mismatches.append("tools")
    if result.get("answer") != case["expected_answer"]:
        mismatches.append("answer")
    return {
        "id": case["id"],
        "passed": not mismatches,
        "mismatches": mismatches,
    }


def run_suite(client, cases: list[dict]) -> dict:
    results = []
    for case in cases:
        actual = run_case(client, case)
        results.append(score_case(actual, case))
    n_pass = sum(1 for r in results if r["passed"])
    return {
        "total": len(results),
        "passed": n_pass,
        "failed": len(results) - n_pass,
        "results": results,
    }


if __name__ == "__main__":
    data_path = Path(__file__).parent / "data" / "golden_cases.json"
    cases = json.loads(data_path.read_text())
    print("Golden suite — scripted LLM, no API key\n")
    scored = []
    for case in cases:
        client = make_scripted_client(case["scripted_responses"])
        actual = run_case(client, case)
        result = score_case(actual, case)
        scored.append(result)
        mark = "PASS" if result["passed"] else "FAIL"
        extra = f"  ({','.join(result['mismatches'])})" if result["mismatches"] else ""
        print(f"  [{mark}] {case['id']}{extra}")
    n_pass = sum(1 for r in scored if r["passed"])
    print(f"\n{n_pass}/{len(cases)} passed")
