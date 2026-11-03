"""Part 1: Who owns the control flow - one task, four strategies.

Every strategy answers the same question with the same tools. The only thing
that changes is who decides what happens next: your code, or the model.

Run alone:  python module-08-structured-workflows/demo/01_control_flow.py
"""

from __future__ import annotations

import json

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from workflow_tools import (
    MODEL,
    Meter,
    Timer,
    reset_state,
    run_tool,
    schemas_for,
)

load_dotenv()

TASK = (
    "Is mission MSN-001 safe to continue? Check the reactor and the shields, "
    "look for any engineering concerns in the logs, and give a go/no-go call."
)

STEP_TOOLS = schemas_for("check_system", "search_logs", "lookup_mission")


def synthesise(task: str, findings: list[str], client: OpenAI, meter: Meter) -> str:
    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=[
            {
                "role": "system",
                "content": (
                    "You are the duty officer. Using only the findings provided, "
                    "give a short readiness assessment ending with GO or NO-GO."
                ),
            },
            {"role": "user", "content": f"Task: {task}\n\nFindings:\n" + "\n".join(findings)},
        ],
    )
    meter.record_llm(response)
    return response.output_text


# ---------------------------------------------------------------------------
# 1. Fixed chain - code decides everything
# ---------------------------------------------------------------------------

def run_fixed_chain(client: OpenAI) -> tuple[str, Meter]:
    meter = Meter()
    with Timer(meter):
        findings = []
        for name, args in [
            ("check_system", {"system": "reactor"}),
            ("check_system", {"system": "shields"}),
            ("search_logs", {"query": "warp core plasma conduit maintenance"}),
        ]:
            meter.decide("code", f"{name}({json.dumps(args)})")
            findings.append(run_tool(name, args, meter))

        meter.decide("code", "synthesise")
        answer = synthesise(TASK, findings, client, meter)
    return answer, meter


# ---------------------------------------------------------------------------
# 2. Router - the model picks a branch, code runs it
# ---------------------------------------------------------------------------

class Route(BaseModel):
    branch: str


BRANCHES = {
    "systems": [("check_system", {"system": "reactor"}), ("check_system", {"system": "shields"})],
    "logs": [("search_logs", {"query": "engineering concern fault damage"})],
    "full": [
        ("check_system", {"system": "reactor"}),
        ("check_system", {"system": "shields"}),
        ("search_logs", {"query": "engineering concern fault damage"}),
    ],
}


def run_router(client: OpenAI) -> tuple[str, Meter]:
    meter = Meter()
    with Timer(meter):
        response = client.responses.parse(
            model=MODEL,
            reasoning={"effort": "none"},
            text_format=Route,
            input=[
                {
                    "role": "system",
                    "content": (
                        "Choose the branch that answers the request. "
                        "Reply with exactly one of: systems, logs, full."
                    ),
                },
                {"role": "user", "content": TASK},
            ],
        )
        meter.record_llm(response)
        parsed = response.output_parsed
        branch = parsed.branch if parsed and parsed.branch in BRANCHES else "full"
        meter.decide("model", f"route -> {branch}")

        findings = []
        for name, args in BRANCHES[branch]:
            meter.decide("code", f"{name}({json.dumps(args)})")
            findings.append(run_tool(name, args, meter))

        meter.decide("code", "synthesise")
        answer = synthesise(TASK, findings, client, meter)
    return answer, meter


# ---------------------------------------------------------------------------
# 3. Plan-and-execute - the model decides once, code runs the plan
# ---------------------------------------------------------------------------

class PlannedStep(BaseModel):
    number: int
    description: str


class Plan(BaseModel):
    steps: list[PlannedStep]


def execute_step(description: str, client: OpenAI, meter: Meter, max_turns: int = 3) -> str:
    messages = [
        {
            "role": "system",
            "content": "Carry out this one step using the tools. Reply with a concise result.",
        },
        {"role": "user", "content": description},
    ]
    for _ in range(max_turns):
        response = client.responses.create(
            model=MODEL,
            reasoning={"effort": "none"},
            input=messages,
            tools=STEP_TOOLS,
            tool_choice="auto",
        )
        meter.record_llm(response)
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            return response.output_text or "(no result)"

        messages += response.output
        for call in calls:
            result = run_tool(call.name, call.arguments, meter)
            messages.append(
                {"type": "function_call_output", "output": result, "call_id": call.call_id}
            )
    return "(step did not finish)"


def run_plan_execute(client: OpenAI) -> tuple[str, Meter]:
    meter = Meter()
    with Timer(meter):
        response = client.responses.parse(
            model=MODEL,
            reasoning={"effort": "none"},
            text_format=Plan,
            input=[
                {
                    "role": "system",
                    "content": (
                        "Break the request into 2-4 concrete steps. Each step must be "
                        "achievable with one tool: check_system, search_logs, or lookup_mission."
                    ),
                },
                {"role": "user", "content": TASK},
            ],
        )
        meter.record_llm(response)
        plan = response.output_parsed
        steps = plan.steps if plan else []
        meter.decide("model", f"plan ({len(steps)} steps)")

        findings = []
        for step in steps:
            meter.decide("code", f"run step {step.number}")
            result = execute_step(step.description, client, meter)
            findings.append(f"{step.description} -> {result}")

        meter.decide("code", "synthesise")
        answer = synthesise(TASK, findings, client, meter)
    return answer, meter


# ---------------------------------------------------------------------------
# 4. ReAct - the model decides every step
# ---------------------------------------------------------------------------

def run_react(client: OpenAI, max_steps: int = 8) -> tuple[str, Meter]:
    meter = Meter()
    messages = [
        {
            "role": "system",
            "content": (
                "You are the duty officer. Use the tools to investigate, then give a "
                "short readiness assessment ending with GO or NO-GO."
            ),
        },
        {"role": "user", "content": TASK},
    ]

    with Timer(meter):
        answer = "(step budget exhausted)"
        for _ in range(max_steps):
            response = client.responses.create(
                model=MODEL,
                reasoning={"effort": "none"},
                input=messages,
                tools=STEP_TOOLS,
                tool_choice="auto",
            )
            meter.record_llm(response)
            calls = [item for item in response.output if item.type == "function_call"]

            if not calls:
                meter.decide("model", "answer")
                answer = response.output_text
                break

            messages += response.output
            for call in calls:
                meter.decide("model", f"{call.name}({call.arguments})")
                result = run_tool(call.name, call.arguments, meter)
                messages.append(
                    {"type": "function_call_output", "output": result, "call_id": call.call_id}
                )
    return answer, meter


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

STRATEGIES = [
    ("Fixed chain", run_fixed_chain),
    ("Router", run_router),
    ("Plan-and-execute", run_plan_execute),
    ("ReAct", run_react),
]


def demo_control_flow(client: OpenAI):
    print("=" * 72)
    print("PART 1: WHO OWNS THE CONTROL FLOW")
    print("=" * 72)
    print()
    print(f"  Task: {TASK}\n")
    print("  The same task, four strategies, the same tools.")
    print("  Watch the 'model decisions' column - that is the part you cannot unit test.\n")

    results = []
    for label, strategy in STRATEGIES:
        reset_state()
        print(f"  --- {label} ---")
        answer, meter = strategy(client)

        for who, what in meter.decisions:
            marker = "code " if who == "code" else "MODEL"
            print(f"      [{marker}] {what}")
        print(f"\n      Answer: {answer.strip()[:200]}\n")
        results.append((label, meter))

    print("=" * 72)
    header = (
        f"  {'Strategy':<20} {'LLM':>5} {'Tools':>6} {'Tokens':>8} "
        f"{'Seconds':>8} {'Model decisions':>16}"
    )
    print(header)
    print("  " + "-" * 68)
    for label, meter in results:
        print(
            f"  {label:<20} {meter.llm_calls:>5} {meter.tool_calls:>6} "
            f"{meter.tokens:>8} {meter.seconds:>8.1f} {meter.model_decisions:>16}"
        )
    print()
    print("  Going down the table you hand the model more of the control flow.")
    print("  It buys adaptability. It costs tokens, latency, and testability.")
    print("  Pick the highest row that still answers the question.")
    print()


if __name__ == "__main__":
    demo_control_flow(OpenAI())
