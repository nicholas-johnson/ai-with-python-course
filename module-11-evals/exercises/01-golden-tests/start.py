"""
Exercise 01 — Golden Tests

Freeze the outcome you accept for a question, then re-run a later build of the
agent and compare. The golden file holds only the question and the accepted
outcome; what the agent does comes from the build under test.

Two builds ship with this exercise. Build A is what you released. Build B has
had its prompt changed and has drifted. Your harness should pass A and fail B.

A case is scored as the mean of four criteria, each in [0, 1]. Tool calls are
structured, so they exact-match: 0 or 1. Prose never matches exactly, so an
LLM judge scores correctness, completeness, and relevance.

No API key: each build replays its own recorded behaviour, and the judge
verdicts are canned.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

DATA_DIR = Path(__file__).parent / "data"

# ---------------------------------------------------------------------------
# Ship tools — provided. Focus on the eval harness below.
# ---------------------------------------------------------------------------

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

# A case passes when its mean criterion score reaches this floor.
PASS_THRESHOLD = 0.8

JUDGE_CRITERIA = ("correctness", "completeness", "relevance")


def load_cases() -> list[dict]:
    """The golden file: questions and the outcomes we accept. Provided."""
    return json.loads((DATA_DIR / "golden_cases.json").read_text())


def load_build(name: str) -> dict:
    """One build's recorded behaviour, keyed by question. Provided."""
    return json.loads((DATA_DIR / "builds.json").read_text())[name]


def make_canned_judge(build_name: str):
    """
    A stand-in for the judge model, so this runs with no API key. Provided.

    Returns a callable with the same shape as a real judge:
        judge(case_id, question, answer, reference) -> dict

    The dict carries a 1-5 score for each of correctness, completeness and
    relevance, plus an explanation — exactly what `llm_judge` returns in
    exercise 03.
    """
    verdicts = json.loads((DATA_DIR / "judge_scores.json").read_text())[build_name]

    def judge(case_id: str, question: str, answer: str | None, reference: str) -> dict:
        return verdicts[case_id]

    return judge


def normalise(score: int) -> float:
    """A 1-5 rubric score onto [0, 1], so every criterion shares one scale. Provided."""
    return (score - 1) / 4


def make_scripted_client(build: dict):
    """
    Build a fake OpenAI client that replays one build of the agent.

    `build` maps a question to the turns that build produces for it. Each turn
    is either {"tool_calls": [{"id", "name", "arguments"}]} or
    {"content": "final answer"}. The client reads the question off the input
    messages, so one client serves the whole suite — same as a real one.
    """
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
    """
    Run the agent loop for one golden case against `client`.

    Args:
        client: OpenAI-shaped client (real or mock). Must expose
            client.responses.create(...).
        case: Golden case with at least a "question" key.
        max_steps: Cap on model turns.

    Returns:
        {"tools": [{"name": str, "arguments": dict}, ...], "answer": str | None}

    TODO:
    - Start messages with SYSTEM_PROMPT and case["question"].
    - Loop up to max_steps:
        call client.responses.create(model=MODEL, reasoning={"effort": "none"}, input=..., tools=TOOLS)
        calls = [item for item in response.output if item.type == "function_call"]
        if calls: messages += response.output, run HANDLERS[call.name], record
            {name, arguments}, append function_call_output items
        elif response.output_text: set answer and break
    - Return tools + answer.
    """
    # TODO: implement the golden-case agent loop
    pass


def score_case(result: dict, case: dict, judge) -> dict:
    """
    Score one case on four criteria, each in [0, 1], and average them.

    Args:
        result: Output of run_case — {"tools": [...], "answer": str | None}.
        case: Golden case with "id", "question", "expected_tools", "expected_answer".
        judge: Callable judge(case_id, question, answer, reference) -> dict with
            1-5 scores for correctness, completeness, relevance, plus an
            explanation. Use make_canned_judge, or ex03's llm_judge.

    Returns:
        {
            "id": str,
            "score": float,            # mean of the four criteria, in [0, 1]
            "criteria": dict,          # each criterion, in [0, 1]
            "passed": bool,            # score >= PASS_THRESHOLD
            "explanation": str,        # why the judge scored the prose that way
        }

    TODO:
    - Call the judge with case["id"], case["question"], result["answer"] and
      case["expected_answer"].
    - Build the criteria dict:
        "tools" is 1.0 when result["tools"] == case["expected_tools"], else 0.0
          (exact list + dicts — tool calls are structured, so they match or not)
        each name in JUDGE_CRITERIA is normalise(verdict[name])
    - score is the mean of the criteria values.
    - passed is score >= PASS_THRESHOLD.
    """
    # TODO: implement scoring
    pass


def run_suite(client, cases: list[dict], judge) -> dict:
    """
    Run every case against one build, score each one, and average the scores.

    Returns:
        {
            "total": int,
            "passed": int,
            "failed": int,
            "suite": float,            # mean of the per-case scores, in [0, 1]
            "results": list[dict],     # score_case outputs
        }

    TODO:
    - For each case, run_case then score_case.
    - Count passed/failed, and average result["score"] for the suite.
    - An empty suite scores 0.0 rather than dividing by zero.
    """
    # TODO: implement the suite runner
    pass


def _format_tools(tools: list[dict]) -> str:
    """Render a tool list for the report. Provided."""
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
        summary = run_suite(
            make_scripted_client(load_build(build_name)),
            cases,
            make_canned_judge(build_name),
        )
        if summary is None:
            print(f"  {build_name} ({note}): not implemented\n")
            continue

        print(f"  {build_name} ({note})")
        for result in summary["results"]:
            mark = "PASS" if result["passed"] else "FAIL"
            criteria = result["criteria"]
            print(f"    [{mark}] {result['id']:24} score={result['score']:.2f}")
            print(
                "           "
                + "  ".join(f"{name}={criteria[name]:.2f}" for name in criteria)
            )
            print(f"           judge: {result['explanation']}")
            if criteria["tools"] < 1.0:
                print(f"           expected  {_format_tools(by_id[result['id']]['expected_tools'])}")
        print(
            f"    suite={summary['suite']:.2f}  "
            f"{summary['passed']}/{summary['total']} cases passed\n"
        )
