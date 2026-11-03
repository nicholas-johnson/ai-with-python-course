"""
Exercise 03 — Parallel Plans and Approval Gates
================================================
Two things a plan can do that a ReAct loop cannot: run independent steps at
the same time, and stop in the middle to wait for a human.

The tools and the single-step executor are provided in `tools.py`. Your job is
the scheduling, the approval gate, and the checkpoint.

Run:  python start.py
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
    # TODO:
    # 1. client.responses.parse(model=MODEL, reasoning={"effort": "none"},
    #                           text_format=Plan, input=[system, user])
    # 2. If response.output_parsed is None, return []
    # 3. Convert each PlannedStep into a PlanStep, carrying depends_on across
    # 4. Set requires_approval = (step.tool in IRREVERSIBLE)
    #    Do this in CODE, not by asking the model. A plan that marks its own
    #    steps as safe is not a safety control.
    raise NotImplementedError("TODO")


def dependency_levels(steps: list[PlanStep]) -> list[list[PlanStep]]:
    """Group steps into waves. Everything within a wave can run concurrently."""
    # TODO:
    # 1. remaining = {s.step_number: s for s in steps}, done = set(), levels = []
    # 2. While remaining:
    #    a. ready = every step whose depends_on are all in `done`
    #       (treat a dependency that is not in `remaining` as satisfied — it
    #        either finished already or never existed)
    #    b. If nothing is ready you have a cycle: append the rest as one final
    #       wave and break. Do NOT loop forever.
    #    c. Append `ready` as a wave, move those step numbers into `done`
    # 3. Return levels
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# Checkpointing
# ---------------------------------------------------------------------------

def save_state(goal: str, steps: list[PlanStep], approved: list[int]) -> None:
    """Write goal, steps and approvals to CHECKPOINT as JSON."""
    # TODO: json.dumps({"goal": ..., "steps": [asdict(s) for s in steps],
    #                   "approved": approved}, indent=2)
    raise NotImplementedError("TODO")


def load_state() -> tuple[str, list[PlanStep], list[int]] | None:
    """Read the checkpoint back. Return None if there is no checkpoint."""
    # TODO: rebuild each PlanStep with PlanStep(**s) so statuses and results
    # come back intact.
    raise NotImplementedError("TODO")


def approve(goal: str, steps: list[PlanStep], approved: list[int], number: int) -> list[int]:
    """Record approval for one step number, persist, and return the new list."""
    # TODO
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def _context_for(step: PlanStep, steps: list[PlanStep]) -> str:
    """Build the context string for a step from its dependencies' results."""
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

    Must be safe to call again after approval: finished steps are skipped, so
    resuming never repeats a side effect.
    """
    # TODO:
    # 1. For each wave from dependency_levels(steps):
    #    a. pending = steps in this wave whose status is not "done"
    #       (this is what makes resuming safe — never re-run a finished step)
    #    b. If any pending step requires_approval and is not in `approved`:
    #         set its status to "awaiting_approval", save_state(...),
    #         and return "awaiting_approval"
    #    c. If pending is empty, continue to the next wave
    #    d. Run the whole wave at once:
    #         results = await asyncio.gather(
    #             *(execute_step(s.description, _context_for(s, steps), client)
    #               for s in pending))
    #    e. Write each result back, set status to "done", then save_state(...)
    # 2. Return "complete"
    raise NotImplementedError("TODO")


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
