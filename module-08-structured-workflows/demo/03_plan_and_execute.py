"""Part 3: Plan-and-execute - decide once, then carry it out.

ReAct re-decides on every turn. Here the model writes the whole plan up front,
code executes it, and the model is only consulted again if a step fails.

Run alone:  python module-08-structured-workflows/demo/03_plan_and_execute.py
"""
from __future__ import annotations

from dataclasses import dataclass

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from workflow_tools import MODEL, run_tool, schemas_for

load_dotenv()

TOOL_SCHEMAS = schemas_for(
    "check_system", "search_logs", "lookup_mission", "calculator", "take_note", "read_notes"
)


# ---------------------------------------------------------------------------
# Plan-and-Execute
# ---------------------------------------------------------------------------

@dataclass
class PlanStep:
    number: int
    description: str
    status: str = "pending"
    result: str = ""


class PlannedStep(BaseModel):
    number: int
    description: str


class Plan(BaseModel):
    """What the LLM returns. PlanStep adds the runtime status and result."""

    steps: list[PlannedStep]


def generate_plan(goal: str, client: OpenAI) -> list[PlanStep]:
    response = client.responses.parse(
        model=MODEL,
        reasoning={"effort": "none"},
        text_format=Plan,
        input=[
            {
                "role": "system",
                "content": (
                    "You are a planning assistant. Given a goal, break it into 3-6 concrete steps. "
                    "Each step should be a single, actionable task that can use the ship system, "
                    "log search, mission lookup, calculation, or note-taking tools."
                ),
            },
            {"role": "user", "content": goal},
        ],
    )
    plan = response.output_parsed
    if not plan:
        return []
    return [PlanStep(number=s.number, description=s.description) for s in plan.steps]


def execute_step(step: PlanStep, client: OpenAI) -> str:
    """Execute a single plan step using tool-calling."""
    messages = [
        {
            "role": "system",
            "content": (
                "Execute this specific task. Use tools as needed. "
                "Provide a concise result when done."
            ),
        },
        {"role": "user", "content": step.description},
    ]

    for _ in range(3):
        response = client.responses.create(
            model=MODEL,
            reasoning={"effort": "none"},
            input=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        calls = [item for item in response.output if item.type == "function_call"]

        if not calls:
            return response.output_text or "(no result)"

        messages += response.output
        for tc in calls:
            result = run_tool(tc.name, tc.arguments)
            messages.append(
                {"type": "function_call_output", "output": result, "call_id": tc.call_id}
            )

    return "(step timed out)"


def revise_plan(
    remaining: list[PlanStep],
    completed: list[PlanStep],
    failure_reason: str,
    client: OpenAI,
) -> list[PlanStep]:
    completed_text = "\n".join(
        f"  {s.number}. {s.description} -> {s.result}" for s in completed
    )
    remaining_text = "\n".join(
        f"  {s.number}. {s.description}" for s in remaining
    )

    response = client.responses.parse(
        model=MODEL,
        reasoning={"effort": "none"},
        text_format=Plan,
        input=[
            {
                "role": "system",
                "content": (
                    "A step in a plan failed. Revise the remaining steps based on what happened."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Completed steps:\n{completed_text}\n\n"
                    f"Failure: {failure_reason}\n\n"
                    f"Remaining steps to revise:\n{remaining_text}"
                ),
            },
        ],
    )
    plan = response.output_parsed
    start_num = len(completed) + 1
    return [
        PlanStep(number=start_num + i, description=s.description)
        for i, s in enumerate(plan.steps if plan else [])
    ]


def plan_and_execute(goal: str, client: OpenAI, max_replans: int = 1) -> dict:
    plan = generate_plan(goal, client)
    completed: list[PlanStep] = []
    replans_left = max_replans

    print(f"\n  Plan ({len(plan)} steps):")
    for step in plan:
        print(f"    {step.number}. {step.description}")
    print()

    i = 0
    while i < len(plan):
        step = plan[i]
        print(f"  Executing step {step.number}: {step.description}...", end=" ", flush=True)

        try:
            result = execute_step(step, client)
            step.status = "done"
            step.result = result
            completed.append(step)
            print("DONE")
            print(f"    Result: {result[:150]}\n")
            i += 1
        except Exception as e:
            step.status = "failed"
            step.result = str(e)
            print(f"FAILED: {e}")

            if replans_left > 0:
                print("  Re-planning remaining steps...")
                remaining = plan[i + 1:]
                plan = completed + [step] + revise_plan(remaining, completed, str(e), client)
                replans_left -= 1
                i += 1
                print("  Revised plan:")
                for s in plan[i:]:
                    print(f"    {s.number}. {s.description}")
                print()
            else:
                completed.append(step)
                i += 1

    synthesis_prompt = "\n".join(
        f"{s.number}. {s.description} -> {s.result}" for s in completed
    )
    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=[
            {
                "role": "system",
                "content": "Synthesise the results of these steps into a final answer.",
            },
            {"role": "user", "content": synthesis_prompt},
        ],
    )
    answer = response.output_text
    return {"answer": answer, "plan": completed}


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def demo_plan_and_execute(client: OpenAI):
    print("=" * 72)
    print("PART 3: PLAN-AND-EXECUTE")
    print("=" * 72)
    print()
    print("  The model decides the shape of the work once, up front.")
    print("  Everything after that is code following a list.\n")

    goals = [
        "Assess mission MSN-001: check the reactor and shields, find any "
        "engineering concerns in the logs, and note the overall risk.",
        "Work out how many hours until the shields reach full charge, and "
        "whether the sensor array maintenance fits in that window.",
    ]

    for goal in goals:
        print(f"  Goal: {goal}")
        result = plan_and_execute(goal, client)
        print(f"\n  Final answer: {result['answer']}\n")

    print("  The plan is a list of plain objects. You can print it, show it to")
    print("  a user, store it, or diff it against what actually happened.")
    print("  That is the whole argument for planning: the plan is data.")
    print()


if __name__ == "__main__":
    demo_plan_and_execute(OpenAI())
