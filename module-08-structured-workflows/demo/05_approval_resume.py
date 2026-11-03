"""Part 5: Because the plan is data, it can stop, be inspected, and carry on.

A ReAct loop lives in a Python call stack. Kill the process and the work is
gone, and there is no moment where a human can step in before something
irreversible happens.

A plan is a list of objects. Write it to disk and the workflow gains two
properties you cannot retrofit onto ReAct: it survives a restart, and it can
block on a human.

Run alone:  python module-08-structured-workflows/demo/05_approval_resume.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from workflow_tools import MODEL, reset_state, run_tool

load_dotenv()

CHECKPOINT = Path(__file__).resolve().parent / ".workflow_state.json"

# Code decides what is dangerous, not the model. A plan that could mark its own
# steps as safe is not a safety control.
NEEDS_APPROVAL = {"file_report"}

StepTool = Literal["check_system", "search_logs", "lookup_mission", "file_report"]

GOAL = (
    "Investigate the degraded sensor array on MSN-001 and file an incident "
    "report with your findings."
)


class PlannedStep(BaseModel):
    number: int
    description: str
    tool: StepTool
    tool_input: str


class Plan(BaseModel):
    steps: list[PlannedStep]


PLANNER_PROMPT = (
    "Break the goal into 3-5 steps. Each step uses exactly one tool:\n"
    "- check_system(tool_input: reactor|navigation|life_support|shields|sensors)\n"
    "- search_logs(tool_input: keywords)\n"
    "- lookup_mission(tool_input: a mission ID such as MSN-001)\n"
    "- file_report(tool_input: the report body)\n"
    "Investigate first. Use file_report exactly once, as the final step."
)


def generate_plan(goal: str, client: OpenAI) -> list[dict]:
    response = client.responses.parse(
        model=MODEL,
        reasoning={"effort": "none"},
        text_format=Plan,
        input=[
            {"role": "system", "content": PLANNER_PROMPT},
            {"role": "user", "content": goal},
        ],
    )
    plan = response.output_parsed
    if not plan:
        return []
    return [
        {
            "number": step.number,
            "description": step.description,
            "tool": step.tool,
            "tool_input": step.tool_input,
            "requires_approval": step.tool in NEEDS_APPROVAL,
            "status": "pending",
            "result": "",
        }
        for step in plan.steps
    ]


# ---------------------------------------------------------------------------
# The checkpoint
# ---------------------------------------------------------------------------

def save_state(state: dict) -> None:
    CHECKPOINT.write_text(json.dumps(state, indent=2))


def load_state() -> dict | None:
    if not CHECKPOINT.exists():
        return None
    return json.loads(CHECKPOINT.read_text())


def approve(state: dict, number: int) -> None:
    state.setdefault("approved", []).append(number)
    save_state(state)


def run_plan(state: dict) -> str:
    """Run pending steps in order. Stop at the first unapproved gated step.

    Safe to call repeatedly: finished steps are skipped, so resuming never
    repeats work or re-runs a side effect.
    """
    approved = set(state.get("approved", []))

    for step in state["steps"]:
        if step["status"] == "done":
            print(f"    {step['number']}. {step['description'][:60]} -- already done, skipping")
            continue

        if step["requires_approval"] and step["number"] not in approved:
            step["status"] = "awaiting_approval"
            state["status"] = "awaiting_approval"
            save_state(state)
            print(f"    {step['number']}. {step['description'][:60]}")
            print(f"       BLOCKED: {step['tool']} needs a human to approve it.")
            return "awaiting_approval"

        args = (
            {"title": f"Incident report: {state['goal'][:40]}", "content": step["tool_input"]}
            if step["tool"] == "file_report"
            else {_arg_name(step["tool"]): step["tool_input"]}
        )
        step["result"] = run_tool(step["tool"], args)
        step["status"] = "done"
        save_state(state)
        print(f"    {step['number']}. {step['description'][:60]}")
        print(f"       -> {' '.join(step['result'].split())[:90]}")

    state["status"] = "complete"
    save_state(state)
    return "complete"


def _arg_name(tool: str) -> str:
    return {
        "check_system": "system",
        "search_logs": "query",
        "lookup_mission": "mission_id",
    }[tool]


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def demo_approval_resume(client: OpenAI):
    print("=" * 72)
    print("PART 5: PAUSE, APPROVE, RESUME")
    print("=" * 72)
    print()

    reset_state()
    CHECKPOINT.unlink(missing_ok=True)

    print(f"  Goal: {GOAL}\n")
    steps = generate_plan(GOAL, client)
    if not steps:
        print("  The planner returned nothing. Try again.")
        return

    state = {"goal": GOAL, "steps": steps, "approved": [], "status": "pending"}
    save_state(state)

    print("  Plan:")
    for step in steps:
        gate = "  <-- needs approval" if step["requires_approval"] else ""
        print(f"    {step['number']}. [{step['tool']}] {step['description'][:55]}{gate}")
    print()

    print("  First run:")
    status = run_plan(state)
    print(f"\n  Status: {status}")
    print(f"  Checkpoint written to {CHECKPOINT.name}\n")

    on_disk = load_state()
    done = [s["number"] for s in on_disk["steps"] if s["status"] == "done"]
    blocked = [s["number"] for s in on_disk["steps"] if s["status"] == "awaiting_approval"]
    print(f"  What survived to disk: {len(on_disk['steps'])} steps, "
          f"done={done}, awaiting approval={blocked}")
    print("  The process could exit right here and lose nothing.\n")

    if not blocked:
        print("  The planner did not schedule a gated step this time, so there")
        print("  was nothing to approve. Re-run to try again.\n")
        return

    print("-" * 72)
    print("  A human reviews the plan and approves the write.\n")

    # Reload from scratch, the way a fresh process would.
    resumed = load_state()
    approve(resumed, blocked[0])

    print("  Second run, resuming from the checkpoint:")
    status = run_plan(resumed)
    print(f"\n  Status: {status}\n")

    print("  Note the already-done steps were skipped, not repeated. That")
    print("  matters the moment a step books a flight or files a report.")
    print("  Durability and human approval both fall out of one decision:")
    print("  write the plan down before you run it.")
    print()


if __name__ == "__main__":
    demo_approval_resume(OpenAI())
