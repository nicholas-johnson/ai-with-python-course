"""
Exercise 02 — Plan-and-Execute (Solution)
============================================
Separate planning from execution: LLM plans, ReAct executes each step.

Run:  python solution.py
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from openai import OpenAI

from react_agent import run_react, TOOLS, print_trace


@dataclass
class PlanStep:
    step_number: int
    description: str
    status: str = "pending"
    result: str = ""


PLAN_SYSTEM = (
    "You are a planning assistant. Given a user query, break it down into a numbered "
    "list of concrete steps that a research agent can execute one at a time.\n\n"
    "Return a JSON object with a single key 'steps' containing an array.\n"
    "Each element: {\"step_number\": int, \"description\": str}\n\n"
    "Rules:\n"
    "- Each step should be a single, focused action\n"
    "- Steps should be in logical order\n"
    "- 2-6 steps for most queries\n"
    "- The final step should always be to compile/summarize the findings"
)

REVISE_SYSTEM = (
    "You are a planning assistant. A multi-step plan is partially complete. "
    "Some steps succeeded and some failed. Revise the remaining steps to account "
    "for what happened.\n\n"
    "Return a JSON object with a single key 'steps' containing an array.\n"
    "Each element: {\"step_number\": int, \"description\": str}\n"
    "Number the steps starting from where you left off."
)


def generate_plan(query: str, client: OpenAI) -> list[PlanStep]:
    """Ask the LLM to create a numbered plan. Returns list of PlanStep."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": PLAN_SYSTEM},
            {"role": "user", "content": query},
        ],
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)
    steps_data = data.get("steps", [])

    return [
        PlanStep(
            step_number=s.get("step_number", i + 1),
            description=s["description"],
        )
        for i, s in enumerate(steps_data)
    ]


def execute_step(
    step: PlanStep,
    previous_results: list[dict],
    client: OpenAI,
) -> dict:
    """Execute a single plan step using the ReAct agent. Returns result dict."""
    context_parts = []
    for prev in previous_results:
        context_parts.append(
            f"Step {prev['step_number']}: {prev['description']}\n"
            f"Result: {prev['result']}"
        )

    query = f"Task: {step.description}"
    if context_parts:
        context = "\n\n".join(context_parts)
        query = f"Context from previous steps:\n{context}\n\n{query}"

    return run_react(query, client)


def revise_plan(
    plan: list[PlanStep],
    results: list[dict],
    original_query: str,
    client: OpenAI,
) -> list[PlanStep]:
    """Revise remaining plan steps after a failure. Returns new steps."""
    completed = [s for s in plan if s.status == "done"]
    remaining = [s for s in plan if s.status in ("pending", "failed")]

    context = f"Original query: {original_query}\n\n"
    if completed:
        context += "Completed steps:\n"
        for s in completed:
            context += f"  Step {s.step_number}: {s.description} → {s.result[:200]}\n"
    if remaining:
        context += "\nRemaining/failed steps:\n"
        for s in remaining:
            context += f"  Step {s.step_number}: {s.description} (status: {s.status})\n"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": REVISE_SYSTEM},
            {"role": "user", "content": context},
        ],
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)
    steps_data = data.get("steps", [])

    start_num = max((s.step_number for s in completed), default=0) + 1
    return [
        PlanStep(
            step_number=s.get("step_number", start_num + i),
            description=s["description"],
        )
        for i, s in enumerate(steps_data)
    ]


def plan_and_execute(query: str, client: OpenAI) -> dict:
    """Full plan-and-execute loop. Returns {"answer": str, "plan": list[PlanStep]}."""
    plan = generate_plan(query, client)
    print_plan(plan)

    results: list[dict] = []
    i = 0
    while i < len(plan):
        step = plan[i]
        step.status = "running"
        print(f"  \u25b6\ufe0f  Executing step {step.step_number}: {step.description}")

        try:
            react_result = execute_step(step, results, client)
            step.status = "done"
            step.result = react_result["answer"]
            results.append({
                "step_number": step.step_number,
                "description": step.description,
                "result": step.result,
            })
            print(f"  \u2705 Done: {step.result[:100]}\n")
        except Exception as e:
            step.status = "failed"
            step.result = str(e)
            print(f"  \u274c Failed: {e}\n")

            print("  Revising plan...")
            new_steps = revise_plan(plan, results, query, client)
            plan = [s for s in plan if s.status == "done"] + new_steps
            print_plan(plan)
            i = next(
                (j for j, s in enumerate(plan) if s.status == "pending"),
                len(plan),
            )
            continue

        i += 1

    summary_parts = []
    for r in results:
        summary_parts.append(f"Step {r['step_number']}: {r['result']}")
    combined = "\n".join(summary_parts)

    final_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Summarize the results of a multi-step research plan into a clear, concise answer.",
            },
            {
                "role": "user",
                "content": f"Original question: {query}\n\nStep results:\n{combined}",
            },
        ],
    )
    answer = final_response.choices[0].message.content or combined

    return {"answer": answer, "plan": plan}


def print_plan(plan: list[PlanStep]) -> None:
    """Pretty-print a plan with step status."""
    status_icons = {
        "pending": "\u23f3",
        "running": "\u25b6\ufe0f",
        "done": "\u2705",
        "failed": "\u274c",
    }
    print("\n  === Plan ===")
    for step in plan:
        icon = status_icons.get(step.status, "?")
        print(f"  {icon} Step {step.step_number}: {step.description}")
        if step.result:
            preview = step.result[:100]
            print(f"     Result: {preview}")
    print()


def main():
    client = OpenAI()
    last_plan: list[PlanStep] = []
    last_query = ""

    print("=== Plan-and-Execute Agent ===")
    print("Commands: /plan, /react <query>, /replan, quit\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            break

        if user_input == "/plan":
            if last_plan:
                print_plan(last_plan)
            else:
                print("[No plan yet]\n")
            continue

        if user_input.startswith("/react "):
            react_query = user_input[7:].strip()
            if react_query:
                print("[Running pure ReAct for comparison...]\n")
                result = run_react(react_query, client)
                print_trace(result["trace"])
                print(f"\nReAct Answer: {result['answer']}\n")
            continue

        if user_input == "/replan":
            if last_query:
                print("[Re-planning...]\n")
                result = plan_and_execute(last_query, client)
                last_plan = result["plan"]
                print(f"\nAnswer: {result['answer']}\n")
            else:
                print("[No previous query to re-plan]\n")
            continue

        last_query = user_input
        result = plan_and_execute(user_input, client)
        last_plan = result["plan"]
        print(f"\nAnswer: {result['answer']}\n")


if __name__ == "__main__":
    main()
