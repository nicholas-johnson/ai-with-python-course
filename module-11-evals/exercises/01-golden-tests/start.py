"""
Exercise 01 — Golden Tests

Regression-test a tool-calling agent with a mock LLM.
No API key: scripted responses drive the loop.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

# ---------------------------------------------------------------------------
# Ship tools — provided. Focus on the eval harness below.
# ---------------------------------------------------------------------------

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_crew_count",
            "description": "Count crew in a department.",
            "parameters": {
                "type": "object",
                "properties": {"department": {"type": "string"}},
                "required": ["department"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ship_status",
            "description": "Status of a ship system (warp, shields, sensors, life_support).",
            "parameters": {
                "type": "object",
                "properties": {"system": {"type": "string"}},
                "required": ["system"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_crew",
            "description": "Search crew by name or role.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
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
    """
    Build a fake OpenAI client from a list of response dicts.

    Each dict is either {"tool_calls": [{"id", "name", "arguments"}]}
    or {"content": "final answer"}.
    """
    queue = list(scripted_responses)

    def _to_message(item: dict):
        if "tool_calls" in item:
            calls = []
            for tc in item["tool_calls"]:
                args = tc["arguments"]
                if not isinstance(args, str):
                    args = json.dumps(args)
                calls.append(
                    SimpleNamespace(
                        id=tc.get("id", "call_0"),
                        function=SimpleNamespace(name=tc["name"], arguments=args),
                    )
                )
            return SimpleNamespace(content=None, tool_calls=calls)
        return SimpleNamespace(content=item.get("content", ""), tool_calls=None)

    def create(**kwargs):
        if not queue:
            raise RuntimeError("Scripted client has no more responses")
        message = _to_message(queue.pop(0))
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def run_case(client, case: dict, max_steps: int = 5) -> dict:
    """
    Run the agent loop for one golden case against `client`.

    Args:
        client: OpenAI-shaped client (real or mock). Must expose
            client.chat.completions.create(...).
        case: Golden case with at least a "question" key.
        max_steps: Cap on model turns.

    Returns:
        {"tools": [{"name": str, "arguments": dict}, ...], "answer": str | None}

    TODO:
    - Start messages with SYSTEM_PROMPT and case["question"].
    - Loop up to max_steps:
        call client.chat.completions.create(model=MODEL, reasoning_effort="none", messages=..., tools=TOOLS)
        if message.tool_calls: execute HANDLERS, record {name, arguments}, append tool results
        elif message.content: set answer and break
    - Return tools + answer.
    """
    # TODO: implement the golden-case agent loop
    pass


def score_case(result: dict, case: dict) -> dict:
    """
    Compare an actual run to expected tools and answer.

    Args:
        result: Output of run_case — {"tools": [...], "answer": str | None}.
        case: Golden case with "id", "expected_tools", "expected_answer".

    Returns:
        {
            "id": str,
            "passed": bool,
            "mismatches": list[str],  # subset of ["tools", "answer"]
        }

    TODO:
    - "tools" mismatches if result["tools"] != case["expected_tools"] (exact list + dicts).
    - "answer" mismatches if result["answer"] != case["expected_answer"].
    - passed is True when mismatches is empty.
    """
    # TODO: implement scoring
    pass


def run_suite(client, cases: list[dict]) -> dict:
    """
    Run every case with the same client and score each one.

    Returns:
        {
            "total": int,
            "passed": int,
            "failed": int,
            "results": list[dict],  # score_case outputs
        }

    TODO:
    - For each case, run_case then score_case.
    - Count passed/failed.
    """
    # TODO: implement the suite runner
    pass


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
        mark = "PASS" if result and result.get("passed") else "FAIL"
        mismatches = ",".join(result.get("mismatches", [])) if result else "not implemented"
        print(f"  [{mark}] {case['id']}" + (f"  ({mismatches})" if mismatches else ""))
    n_pass = sum(1 for r in scored if r and r.get("passed"))
    print(f"\n{n_pass}/{len(cases)} passed")
