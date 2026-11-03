"""Part 4: A plan is a graph, not a list - so run the independent steps at once.

This is the thing ReAct cannot do. ReAct picks its next action *after* reading
the last observation, so every step is serialised by construction. A plan
written up front can declare which steps actually depend on each other, and
everything else runs concurrently.

Run alone:  python module-08-structured-workflows/demo/04_parallel_plan.py
"""

from __future__ import annotations

import asyncio
import time

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel

from workflow_tools import MODEL, TOOL_LATENCY, run_tool, schemas_for

load_dotenv()

STEP_TOOLS = schemas_for("check_system", "search_logs", "lookup_mission", "calculator")

GOAL = (
    "Produce a full readiness report for mission MSN-001: the reactor, shields, "
    "life support and sensors, plus any engineering concerns in the logs, "
    "then an overall go/no-go."
)


class PlannedStep(BaseModel):
    number: int
    description: str
    depends_on: list[int]


class Plan(BaseModel):
    steps: list[PlannedStep]


PLANNER_PROMPT = (
    "Break the goal into 4-7 concrete steps. Each step must be achievable with a "
    "single tool call: check_system, search_logs, lookup_mission or calculator.\n"
    "For each step, set `depends_on` to the list of step numbers whose results it "
    "genuinely needs. Independent steps must have an empty list - they will be run "
    "concurrently, so do not invent dependencies to force an order."
)


def generate_plan(goal: str, client: OpenAI) -> list[PlannedStep]:
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
    return list(plan.steps) if plan else []


# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------

def dependency_levels(steps: list[PlannedStep]) -> list[list[PlannedStep]]:
    """Group steps into waves. Everything in a wave can run at the same time.

    Steps whose dependencies are missing or circular are swept into a final
    wave rather than dropped, so a confused plan still runs.
    """
    remaining = {step.number: step for step in steps}
    done: set[int] = set()
    levels: list[list[PlannedStep]] = []

    while remaining:
        ready = [
            step
            for step in remaining.values()
            if all(dep in done or dep not in remaining for dep in step.depends_on)
        ]
        if not ready:
            levels.append(list(remaining.values()))
            break
        levels.append(ready)
        for step in ready:
            done.add(step.number)
            del remaining[step.number]

    return levels


async def execute_step(
    step: PlannedStep, context: dict[int, str], client: AsyncOpenAI, max_turns: int = 3
) -> str:
    """Run one step. Results of its dependencies are passed in as context."""
    prior = "\n".join(f"Step {n} result: {context[n]}" for n in step.depends_on if n in context)
    messages = [
        {
            "role": "system",
            "content": "Carry out this one step using the tools. Reply with a concise result.",
        },
        {"role": "user", "content": f"{step.description}\n\n{prior}".strip()},
    ]

    for _ in range(max_turns):
        response = await client.responses.create(
            model=MODEL,
            reasoning={"effort": "none"},
            input=messages,
            tools=STEP_TOOLS,
            tool_choice="auto",
        )
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            return response.output_text or "(no result)"

        messages += response.output
        for call in calls:
            # The tool itself is blocking, so hand it to a worker thread rather
            # than stalling the event loop and serialising the whole wave.
            result = await asyncio.to_thread(run_tool, call.name, call.arguments)
            messages.append(
                {"type": "function_call_output", "output": result, "call_id": call.call_id}
            )
    return "(step did not finish)"


async def run_serial(steps: list[PlannedStep], client: AsyncOpenAI) -> tuple[dict[int, str], float]:
    start = time.perf_counter()
    results: dict[int, str] = {}
    for step in steps:
        results[step.number] = await execute_step(step, results, client)
    return results, time.perf_counter() - start


async def run_parallel(
    levels: list[list[PlannedStep]], client: AsyncOpenAI
) -> tuple[dict[int, str], float]:
    start = time.perf_counter()
    results: dict[int, str] = {}
    for wave in levels:
        completed = await asyncio.gather(
            *(execute_step(step, results, client) for step in wave)
        )
        for step, result in zip(wave, completed, strict=True):
            results[step.number] = result
    return results, time.perf_counter() - start


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def print_plan(steps: list[PlannedStep], levels: list[list[PlannedStep]]) -> None:
    print(f"  Plan ({len(steps)} steps):")
    for step in steps:
        deps = ", ".join(str(d) for d in step.depends_on) or "-"
        print(f"    {step.number}. [after: {deps}] {step.description}")
    print()
    print(f"  Scheduled into {len(levels)} waves:")
    for i, wave in enumerate(levels, start=1):
        numbers = ", ".join(str(s.number) for s in wave)
        print(f"    Wave {i}: steps {numbers}  ({len(wave)} concurrent)")
    print()


async def _run(client: OpenAI):
    print(f"  Goal: {GOAL}\n")
    steps = generate_plan(GOAL, client)
    if not steps:
        print("  The planner returned nothing. Try again.")
        return

    levels = dependency_levels(steps)
    print_plan(steps, levels)

    async_client = AsyncOpenAI()
    print("  Running the plan serially, one step after another...")
    _, serial_seconds = await run_serial(steps, async_client)
    print(f"    {serial_seconds:.1f}s\n")

    print("  Running the same plan wave by wave...")
    results, parallel_seconds = await run_parallel(levels, async_client)
    print(f"    {parallel_seconds:.1f}s\n")

    speedup = serial_seconds / parallel_seconds if parallel_seconds else 1.0
    widest = max(len(wave) for wave in levels)
    print(f"  {speedup:.1f}x faster, from {len(steps)} steps in {len(levels)} waves")
    print(f"  (widest wave: {widest} steps at once)\n")

    for number in sorted(results):
        print(f"    {number}. {' '.join(results[number].split())[:100]}")
    print()


def demo_parallel_plan(client: OpenAI):
    print("=" * 72)
    print("PART 4: THE PLAN IS A GRAPH")
    print("=" * 72)
    print()
    print("  Adding one field to the plan schema - depends_on - turns a list")
    print("  into a dependency graph you can schedule.\n")
    asyncio.run(_run(client))
    print("  ReAct cannot do this. It chooses its next action from the last")
    print("  observation, so it is serial whether or not the work really is.")
    print(f"  (Each tool here sleeps {TOOL_LATENCY}s to stand in for a real call.)")
    print()


if __name__ == "__main__":
    demo_parallel_plan(OpenAI())
