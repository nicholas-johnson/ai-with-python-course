"""
Exercise 01 — Golden Tests (Solution)

One frozen reference, two builds of the agent. Build A matches the reference;
build B has drifted and the suite says where.

A case scores the mean of four criteria in [0, 1]: an exact match on the tool
calls, plus correctness, completeness and relevance from a judge.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

DATA_DIR = Path(__file__).parent / "data"

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
    "command": [{"name": "Commander Elara Voss", "role": "captain"}],
    "science": [
        {"name": "Lt. Cmdr. Kael Orin", "role": "science-officer"},
        {"name": "Specialist Juno Park", "role": "science-officer"},
        {"name": "Dr. Felix Strand", "role": "science-officer"},
    ],
    "engineering": [
        {"name": "Chief Engineer Mira Chen", "role": "engineer"},
        {"name": "Ensign Tomás Herrera", "role": "engineer"},
    ],
    "operations": [
        {"name": "Lt. Zara Petrov", "role": "navigator"},
        {"name": "Ensign Dax Morel", "role": "ops"},
        {"name": "Lt. Cmdr. Aisha Okonkwo", "role": "navigator"},
        {"name": "Specialist Bodhi Kwan", "role": "ops"},
    ],
    "medical": [{"name": "Dr. Sable Achebe", "role": "medical-officer"}],
    "security": [{"name": "Lt. Reiko Tanaka", "role": "security-chief"}],
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

PASS_THRESHOLD = 0.8

JUDGE_CRITERIA = ("correctness", "completeness", "relevance")


def load_cases() -> list[dict]:
    return json.loads((DATA_DIR / "golden_cases.json").read_text())


def load_build(name: str) -> dict:
    return json.loads((DATA_DIR / "builds.json").read_text())[name]


def make_canned_judge(build_name: str):
    """A stand-in for the judge model so this runs with no API key."""
    verdicts = json.loads((DATA_DIR / "judge_scores.json").read_text())[build_name]

    def judge(case_id: str, question: str, answer: str | None, reference: str) -> dict:
        return verdicts[case_id]

    return judge


def normalise(score: int) -> float:
    """A 1-5 rubric score onto [0, 1], so every criterion shares one scale."""
    return (score - 1) / 4


def make_scripted_client(build: dict):
    queues: dict[str, list[dict]] = {}

    def _question_from(messages) -> str:
        for message in messages:
            if isinstance(message, dict) and message.get("role") == "user":
                return message["content"]
        raise RuntimeError("No user message in input")

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
        question = _question_from(kwargs["input"])
        if question not in queues:
            queues[question] = list(build[question])
        queue = queues[question]
        if not queue:
            raise RuntimeError(f"Build has no more responses for: {question}")
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


def score_case(result: dict, case: dict, judge) -> dict:
    verdict = judge(
        case["id"],
        case["question"],
        result.get("answer"),
        case["expected_answer"],
    )
    criteria = {
        "tools": 1.0 if result.get("tools") == case["expected_tools"] else 0.0,
        **{name: normalise(verdict[name]) for name in JUDGE_CRITERIA},
    }
    score = sum(criteria.values()) / len(criteria)
    return {
        "id": case["id"],
        "score": score,
        "criteria": criteria,
        "passed": score >= PASS_THRESHOLD,
        "explanation": verdict["explanation"],
    }


def run_suite(client, cases: list[dict], judge) -> dict:
    results = []
    for case in cases:
        actual = run_case(client, case)
        results.append(score_case(actual, case, judge))
    n_pass = sum(1 for r in results if r["passed"])
    return {
        "total": len(results),
        "passed": n_pass,
        "failed": len(results) - n_pass,
        "suite": sum(r["score"] for r in results) / len(results) if results else 0.0,
        "results": results,
    }


def _format_tools(tools: list[dict]) -> str:
    if not tools:
        return "(no tools called)"
    return ", ".join(
        f"{t['name']}({', '.join(f'{k}={v}' for k, v in t['arguments'].items())})"
        for t in tools
    )


if __name__ == "__main__":
    cases = load_cases()
    by_id = {case["id"]: case for case in cases}
    print("Golden suite — one frozen reference, two builds, no API key\n")

    for build_name, note in (("build-a", "shipped"), ("build-b", "prompt changed")):
        client = make_scripted_client(load_build(build_name))
        judge = make_canned_judge(build_name)
        actuals = {case["id"]: run_case(client, case) for case in cases}
        results = [score_case(actuals[case["id"]], case, judge) for case in cases]
        n_pass = sum(1 for r in results if r["passed"])
        suite = sum(r["score"] for r in results) / len(results)

        print(f"  {build_name} ({note})")
        for result in results:
            case = by_id[result["id"]]
            actual = actuals[result["id"]]
            criteria = result["criteria"]
            mark = "PASS" if result["passed"] else "FAIL"
            print(f"    [{mark}] {result['id']:24} score={result['score']:.2f}")
            print(
                "           "
                + "  ".join(f"{name}={criteria[name]:.2f}" for name in criteria)
            )
            print(f"           judge: {result['explanation']}")
            if criteria["tools"] < 1.0:
                print(f"           expected  {_format_tools(case['expected_tools'])}")
                print(f"           actual    {_format_tools(actual['tools'])}")
        print(f"    suite={suite:.2f}  {n_pass}/{len(results)} cases passed\n")

    print("  ship-status-warp is the regression golden tests exist for: build B")
    print("  stopped calling get_ship_status. Nothing in the golden file told it")
    print("  to call that tool — the build changed, and the suite noticed.\n")
    print("  search-captain is the case a string comparison gets wrong: right")
    print("  facts, reordered clause. The judge scores it 1.00 and it passes.")
