"""Part 1: Golden tests — one frozen reference, two agent builds.

The golden file holds only the question and the outcome we accept. What the
agent actually does comes from the build under test, so the reference never
tells the agent what to do. Build A matches the reference. Build B has had
its prompt changed and drifts — and the suite catches it.

Scoring is a mean of criteria in [0, 1]. Tool calls are structured, so they
exact-match: 0 or 1. Prose never matches exactly, so an LLM judge scores it on
correctness, completeness, and relevance. Average the criteria for a per-case
score, average those for the suite.

Both the build under test and the judge are real API calls in production. Here
both are simulated so the demo runs with no key; the test is the same shape.

Run alone:  python module-11-evals/demo/01_golden.py
"""

import json
from types import SimpleNamespace

CREW = {
    "engineering": [
        {"name": "Mira Chen", "role": "Lead Engineer"},
        {"name": "Bodhi Kwan", "role": "Systems Tech"},
    ],
    "command": [{"name": "Elara Voss", "role": "Captain"}],
    "medical": [{"name": "Amara Osei", "role": "Chief Medical Officer"}],
}

SHIP = {
    "warp": {"status": "online", "efficiency": 0.97},
    "shields": {"status": "online", "efficiency": 0.85},
}


def get_crew_count(department):
    return json.dumps({"count": len(CREW.get(department, []))})


def get_ship_status(system):
    return json.dumps(SHIP.get(system, {"error": "unknown system"}))


def search_crew(query):
    needle = query.lower()
    hits = [
        member["name"]
        for members in CREW.values()
        for member in members
        if needle in member["name"].lower() or needle in member["role"].lower()
    ]
    return json.dumps(hits)


HANDLERS = {
    "get_crew_count": get_crew_count,
    "get_ship_status": get_ship_status,
    "search_crew": search_crew,
}

# ---------------------------------------------------------------------------
# The golden file: question in, accepted outcome out. No scripts live here.
# ---------------------------------------------------------------------------

GOLDEN = [
    {
        "id": "crew-engineering",
        "question": "How many people are in engineering?",
        "expected_tools": [
            {"name": "get_crew_count", "arguments": {"department": "engineering"}}
        ],
        "expected_answer": "Engineering has 2 crew members.",
    },
    {
        "id": "warp-status",
        "question": "Is the warp drive healthy?",
        "expected_tools": [{"name": "get_ship_status", "arguments": {"system": "warp"}}],
        "expected_answer": "Warp is online at 97% efficiency.",
    },
    {
        "id": "who-is-captain",
        "question": "Who is the captain?",
        "expected_tools": [{"name": "search_crew", "arguments": {"query": "captain"}}],
        "expected_answer": "Commander Elara Voss is the captain.",
    },
]

# ---------------------------------------------------------------------------
# Two builds of the agent. Swapping the build is the only thing that changes.
# ---------------------------------------------------------------------------

BUILD_A = {
    "How many people are in engineering?": [
        {"tool_calls": [{"name": "get_crew_count", "arguments": {"department": "engineering"}}]},
        {"content": "Engineering has 2 crew members."},
    ],
    "Is the warp drive healthy?": [
        {"tool_calls": [{"name": "get_ship_status", "arguments": {"system": "warp"}}]},
        {"content": "Warp is online at 97% efficiency."},
    ],
    "Who is the captain?": [
        {"tool_calls": [{"name": "search_crew", "arguments": {"query": "captain"}}]},
        {"content": "Commander Elara Voss is the captain."},
    ],
}

BUILD_B = {
    # Reads the wrong department.
    "How many people are in engineering?": [
        {"tool_calls": [{"name": "get_crew_count", "arguments": {"department": "medical"}}]},
        {"content": "Engineering has 1 crew member."},
    ],
    # Stops calling the tool and answers from memory.
    "Is the warp drive healthy?": [
        {"content": "Warp should be fine."},
    ],
    # Right facts, different words.
    "Who is the captain?": [
        {"tool_calls": [{"name": "search_crew", "arguments": {"query": "captain"}}]},
        {"content": "The captain is Commander Elara Voss."},
    ],
}

# ---------------------------------------------------------------------------
# The judge. In production this is one llm_judge call per case, scoring 1-5 on
# each criterion. Here the verdicts are canned so the demo needs no key.
# ---------------------------------------------------------------------------

JUDGE_VERDICTS = {
    ("build-a", "crew-engineering"): {
        "correctness": 5,
        "completeness": 5,
        "relevance": 5,
        "explanation": "Same count, same wording as the reference.",
    },
    ("build-a", "warp-status"): {
        "correctness": 5,
        "completeness": 5,
        "relevance": 5,
        "explanation": "Status and efficiency both match.",
    },
    ("build-a", "who-is-captain"): {
        "correctness": 5,
        "completeness": 5,
        "relevance": 5,
        "explanation": "Names the captain, as the reference does.",
    },
    ("build-b", "crew-engineering"): {
        "correctness": 1,
        "completeness": 2,
        "relevance": 5,
        "explanation": "Says 1 crew member; the reference says 2.",
    },
    ("build-b", "warp-status"): {
        "correctness": 2,
        "completeness": 1,
        "relevance": 4,
        "explanation": "Hedges instead of reporting status and efficiency.",
    },
    ("build-b", "who-is-captain"): {
        "correctness": 5,
        "completeness": 5,
        "relevance": 5,
        "explanation": "Same captain, reordered clause.",
    },
}

PASS_THRESHOLD = 0.8


def _canned_judge(build_name):
    """Stand in for the judge model: one verdict per case, scored 1-5."""

    def judge(case_id, question, answer, reference):
        return JUDGE_VERDICTS[(build_name, case_id)]

    return judge


def _normalise(score):
    """A 1-5 rubric score onto [0, 1], so every criterion shares one scale."""
    return (score - 1) / 4


def _client_for(turns):
    """Stand in for the model: replay one build's behaviour for one question."""
    queue = list(turns)

    def create(**kwargs):
        turn = queue.pop(0)
        if "tool_calls" in turn:
            calls = [
                SimpleNamespace(
                    type="function_call",
                    call_id=f"c{i}",
                    name=tc["name"],
                    arguments=json.dumps(tc["arguments"]),
                )
                for i, tc in enumerate(turn["tool_calls"])
            ]
            return SimpleNamespace(output=calls, output_text="")
        return SimpleNamespace(output=[], output_text=turn["content"])

    return SimpleNamespace(responses=SimpleNamespace(create=create))


def run_case(client, question, max_steps=5):
    """The real agent loop. Returns what the agent did, not what we wanted."""
    tools = []
    answer = None
    messages = [{"role": "user", "content": question}]

    for _ in range(max_steps):
        response = client.responses.create(input=messages)
        calls = [item for item in response.output if item.type == "function_call"]
        if calls:
            messages += response.output
            for call in calls:
                args = json.loads(call.arguments)
                tools.append({"name": call.name, "arguments": args})
                handler = HANDLERS.get(call.name)
                output = handler(**args) if handler else json.dumps({"error": "unknown tool"})
                messages.append(
                    {"type": "function_call_output", "call_id": call.call_id, "output": output}
                )
        elif response.output_text:
            answer = response.output_text
            break

    return {"tools": tools, "answer": answer}


def score_case(actual, case, judge):
    """One case, four criteria in [0, 1], and their mean."""
    verdict = judge(case["id"], case["question"], actual["answer"], case["expected_answer"])
    criteria = {
        "tools": 1.0 if actual["tools"] == case["expected_tools"] else 0.0,
        "correctness": _normalise(verdict["correctness"]),
        "completeness": _normalise(verdict["completeness"]),
        "relevance": _normalise(verdict["relevance"]),
    }
    score = sum(criteria.values()) / len(criteria)
    return {
        "id": case["id"],
        "score": score,
        "criteria": criteria,
        "passed": score >= PASS_THRESHOLD,
        "explanation": verdict["explanation"],
    }


def _fmt_tools(tools):
    if not tools:
        return "(no tools called)"
    return ", ".join(
        f"{t['name']}({', '.join(f'{k}={v}' for k, v in t['arguments'].items())})"
        for t in tools
    )


def run_suite(build, cases, judge):
    """Score every case, then average the per-case scores for the suite."""
    rows = []
    for case in cases:
        actual = run_case(_client_for(build[case["question"]]), case["question"])
        rows.append((case, actual, score_case(actual, case, judge)))
    suite = sum(score["score"] for _, _, score in rows) / len(rows)
    return rows, suite


def demo_golden():
    print("=" * 60)
    print("PART 1: GOLDEN TESTS")
    print("=" * 60)
    print()
    print("  The golden file holds the question and the outcome we accept.")
    print("  The build under test decides what actually happens.")
    print(f"  Each case scores the mean of four criteria; {PASS_THRESHOLD:.2f} passes.")
    print()

    builds = (
        ("build-a", "shipped", BUILD_A),
        ("build-b", "prompt changed", BUILD_B),
    )
    for name, note, build in builds:
        print(f"  {name} ({note})")
        rows, suite = run_suite(build, GOLDEN, _canned_judge(name))
        for case, actual, score in rows:
            mark = "PASS" if score["passed"] else "FAIL"
            criteria = score["criteria"]
            print(f"    [{mark}] {case['id']:16} score={score['score']:.2f}")
            print(
                f"           tools={criteria['tools']:.2f}  "
                f"correctness={criteria['correctness']:.2f}  "
                f"completeness={criteria['completeness']:.2f}  "
                f"relevance={criteria['relevance']:.2f}"
            )
            print(f"           judge: {score['explanation']}")
            if criteria["tools"] < 1.0:
                print(f"           expected  {_fmt_tools(case['expected_tools'])}")
                print(f"           actual    {_fmt_tools(actual['tools'])}")
        passed = sum(1 for _, _, s in rows if s["passed"])
        print(f"    suite={suite:.2f}  {passed}/{len(rows)} cases passed\n")

    print("  warp-status is the regression golden tests exist for: build B")
    print("  stopped calling get_ship_status. Nothing in the golden file told")
    print("  it to call that tool — the build changed, and the suite noticed.")
    print()
    print("  who-is-captain is the case a string comparison gets wrong: right")
    print("  facts, reordered clause. The judge scores it 1.00 and it passes,")
    print("  so the suite reports two regressions rather than three.")
    print()


if __name__ == "__main__":
    demo_golden()
