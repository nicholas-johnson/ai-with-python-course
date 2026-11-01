"""Part 1: Golden tests — one frozen reference, two agent builds.

The golden file holds only the question and the outcome we accept. What the
agent actually does comes from the build under test, so the reference never
tells the agent what to do. Build A matches the reference. Build B has had
its prompt changed and drifts — and the suite catches it.

In production the build under test is a real API call. Here it is simulated
so the demo runs with no key; the structure of the test is the same.

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


def score_case(actual, case):
    mismatches = []
    if actual["tools"] != case["expected_tools"]:
        mismatches.append("tools")
    if actual["answer"] != case["expected_answer"]:
        mismatches.append("answer")
    return {"id": case["id"], "passed": not mismatches, "mismatches": mismatches}


def _fmt_tools(tools):
    if not tools:
        return "(no tools called)"
    return ", ".join(
        f"{t['name']}({', '.join(f'{k}={v}' for k, v in t['arguments'].items())})"
        for t in tools
    )


def run_suite(build, cases):
    rows = []
    for case in cases:
        actual = run_case(_client_for(build[case["question"]]), case["question"])
        rows.append((case, actual, score_case(actual, case)))
    return rows


def demo_golden():
    print("=" * 60)
    print("PART 1: GOLDEN TESTS")
    print("=" * 60)
    print()
    print("  The golden file holds the question and the outcome we accept.")
    print("  The build under test decides what actually happens.")
    print()

    for label, build in (("build-a (shipped)", BUILD_A), ("build-b (prompt changed)", BUILD_B)):
        print(f"  {label}")
        rows = run_suite(build, GOLDEN)
        for case, actual, score in rows:
            mark = "PASS" if score["passed"] else "FAIL"
            detail = ",".join(score["mismatches"])
            print(f"    [{mark}] {case['id']}" + (f"  ({detail})" if detail else ""))
            if "tools" in score["mismatches"]:
                print(f"           expected  {_fmt_tools(case['expected_tools'])}")
                print(f"           actual    {_fmt_tools(actual['tools'])}")
            if "answer" in score["mismatches"]:
                print(f"           expected  {case['expected_answer']}")
                print(f"           actual    {actual['answer']}")
        passed = sum(1 for _, _, s in rows if s["passed"])
        print(f"    {passed}/{len(rows)} passed\n")

    print("  warp-status is the regression golden tests exist for: build B")
    print("  stopped calling get_ship_status. Nothing in the golden file told")
    print("  it to call that tool — the build changed, and the suite noticed.")
    print()
    print("  who-is-captain is a false alarm: the facts are right, the wording")
    print("  moved. Exact match cannot tell those apart. That is part 3's job.")
    print()


if __name__ == "__main__":
    demo_golden()
