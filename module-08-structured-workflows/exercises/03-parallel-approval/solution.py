"""
Exercise 03 — Parallel Plans and Approval Gates (Solution)
==========================================================
Two things a plan can do that a ReAct loop cannot: run independent steps at
the same time, and stop in the middle to wait for a human.

Run:  python solution.py
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel
from tools import IRREVERSIBLE, execute_step, reset_state

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

CHECKPOINT = Path(__file__).resolve().parent / ".workflow_state.json"


@dataclass
class PlanStep:
    step_number: int
    description: str
    tool: str
    depends_on: list[int] = field(default_factory=list)
    requires_approval: bool = False
    status: str = "pending"  # pending | done | awaiting_approval
    result: str = ""


class PlannedStep(BaseModel):
    step_number: int
    description: str
    tool: str
    depends_on: list[int]


class Plan(BaseModel):
    """What the LLM returns. PlanStep adds runtime state the model must not invent."""

    steps: list[PlannedStep]


PLAN_SYSTEM = (
    "You are a travel planning assistant. Break the user's goal into 4-7 concrete steps.\n"
    "Each step uses exactly one tool: research_destination, find_flight, book_flight, "
    "calculator, take_note or search_web.\n"
    "Set `depends_on` to the step numbers whose results the step genuinely needs. "
    "Independent steps must have an empty list — they will run concurrently, so do not "
    "invent an order that is not required.\n"
    "Researching different cities is independent work. Booking always depends on "
    "finding the flight first."
)


def generate_plan(goal: str, client: OpenAI) -> list[PlanStep]:
    """Ask for a plan, then decide in code which steps need a human."""
    response = client.responses.parse(
        model=MODEL,
        reasoning={"effort": "none"},
        text_format=Plan,
        input=[
            {"role": "system", "content": PLAN_SYSTEM},
            {"role": "user", "content": goal},
        ],
    )
    plan = response.output_parsed
    if not plan:
        return []

    return [
        PlanStep(
            step_number=s.step_number,
            description=s.description,
            tool=s.tool,
            depends_on=list(s.depends_on),
            # Code decides, not the model. Never let a plan self-certify.
            requires_approval=s.tool in IRREVERSIBLE,
        )
        for s in plan.steps
    ]


def dependency_levels(steps: list[PlanStep]) -> list[list[PlanStep]]:
    """Group steps into waves. Everything within a wave can run concurrently."""
    remaining = {step.step_number: step for step in steps}
    done: set[int] = set()
    levels: list[list[PlanStep]] = []

    while remaining:
        ready = [
            step
            for step in remaining.values()
            if all(dep in done or dep not in remaining for dep in step.depends_on)
        ]
        if not ready:
            # A cycle, or a dependency that cannot be satisfied. Run the rest
            # together rather than looping forever.
            levels.append(list(remaining.values()))
            break
        levels.append(ready)
        for step in ready:
            done.add(step.step_number)
            del remaining[step.step_number]

    return levels


# ---------------------------------------------------------------------------
# Checkpointing
# ---------------------------------------------------------------------------

def save_state(goal: str, steps: list[PlanStep], approved: list[int]) -> None:
    CHECKPOINT.write_text(
        json.dumps(
            {"goal": goal, "steps": [asdict(s) for s in steps], "approved": approved},
            indent=2,
        )
    )


def load_state() -> tuple[str, list[PlanStep], list[int]] | None:
    if not CHECKPOINT.exists():
        return None
    data = json.loads(CHECKPOINT.read_text())
    steps = [PlanStep(**s) for s in data["steps"]]
    return data["goal"], steps, data.get("approved", [])


def approve(goal: str, steps: list[PlanStep], approved: list[int], number: int) -> list[int]:
    updated = [*approved, number]
    save_state(goal, steps, updated)
    return updated


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def _context_for(step: PlanStep, steps: list[PlanStep]) -> str:
    by_number = {s.step_number: s for s in steps}
    return "\n".join(
        f"Step {n} result: {by_number[n].result}"
        for n in step.depends_on
        if n in by_number and by_number[n].result
    )


async def run_plan(
    goal: str,
    steps: list[PlanStep],
    approved: list[int],
    client: AsyncOpenAI,
) -> str:
    """Run the plan wave by wave, stopping at the first unapproved gated step.

    Safe to call again after approval: finished steps are skipped, so resuming
    never repeats a side effect.
    """
    approved_set = set(approved)

    for wave in dependency_levels(steps):
        pending = [s for s in wave if s.status != "done"]
        for step in pending:
            if step.requires_approval and step.step_number not in approved_set:
                step.status = "awaiting_approval"
                save_state(goal, steps, approved)
                return "awaiting_approval"

        if not pending:
            continue

        results = await asyncio.gather(
            *(execute_step(s.description, _context_for(s, steps), client) for s in pending)
        )
        for step, result in zip(pending, results, strict=True):
            step.result = result
            step.status = "done"
        save_state(goal, steps, approved)

    save_state(goal, steps, approved)
    return "complete"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def print_plan(steps: list[PlanStep]) -> None:
    levels = dependency_levels(steps)
    print(f"\n  Plan ({len(steps)} steps, {len(levels)} waves):")
    for step in steps:
        deps = ", ".join(str(d) for d in step.depends_on) or "-"
        gate = "  <-- needs approval" if step.requires_approval else ""
        mark = {"done": "x", "awaiting_approval": "!", "pending": " "}[step.status]
        print(f"    [{mark}] {step.step_number}. (after: {deps}) {step.description}{gate}")
    for i, wave in enumerate(levels, start=1):
        numbers = ", ".join(str(s.step_number) for s in wave)
        print(f"      wave {i}: {numbers}")
    print()


def main():
    client = OpenAI()
    async_client = AsyncOpenAI()

    goal = None
    steps: list[PlanStep] = []
    approved: list[int] = []

    print("=== Parallel Plans and Approval Gates ===")
    print("Commands: /plan <goal>, /run, /approve N, /state, /reset, quit\n")

    restored = load_state()
    if restored:
        goal, steps, approved = restored
        print(f"[Resumed from checkpoint: {goal}]")
        print_plan(steps)

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input or user_input.lower() == "quit":
            break

        if user_input.startswith("/plan "):
            goal = user_input[len("/plan "):].strip()
            reset_state()
            approved = []
            steps = generate_plan(goal, client)
            save_state(goal, steps, approved)
            print_plan(steps)

        elif user_input == "/run":
            if not steps:
                print("[No plan. Use /plan <goal> first]\n")
                continue
            status = asyncio.run(run_plan(goal, steps, approved, async_client))
            print_plan(steps)
            print(f"[{status}]")
            if status == "awaiting_approval":
                blocked = next(s for s in steps if s.status == "awaiting_approval")
                print(f"[Step {blocked.step_number} needs approval: /approve "
                      f"{blocked.step_number}]")
            print()

        elif user_input.startswith("/approve "):
            try:
                number = int(user_input.split()[1])
            except (IndexError, ValueError):
                print("[Usage: /approve N]\n")
                continue
            approved = approve(goal, steps, approved, number)
            print(f"[Step {number} approved. /run to continue]\n")

        elif user_input == "/state":
            if CHECKPOINT.exists():
                print(CHECKPOINT.read_text())
            else:
                print("[No checkpoint]\n")

        elif user_input == "/reset":
            CHECKPOINT.unlink(missing_ok=True)
            reset_state()
            goal, steps, approved = None, [], []
            print("[Cleared]\n")

        else:
            print("[Unknown command]\n")


if __name__ == "__main__":
    main()
