"""
Module 8 — Demo 02: Plan-and-Execute

Interactive walkthrough of the plan-and-execute pattern.
Generates a complete plan up front, then executes each step.
Shows re-planning when a step fails.

Run:  python module-08-structured-workflows/demo/02_plan_and_execute.py
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
import httpx
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


# ---------------------------------------------------------------------------
# Tools (reused from demo 01)
# ---------------------------------------------------------------------------

_notes: list[str] = []


def search_web(query: str) -> str:
    try:
        resp = httpx.get(
            "https://lite.duckduckgo.com/lite",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        text = re.sub(r"<[^>]+>", " ", resp.text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:2000] if text else "No results found."
    except Exception as e:
        return f"Search error: {e}"


def calculator(expression: str) -> str:
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return "Error: only digits and basic operators allowed"
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"Error: {e}"


def take_note(content: str) -> str:
    _notes.append(content)
    return f"Note saved ({len(_notes)} total)."


def read_notes() -> str:
    if not _notes:
        return "No notes yet."
    return "\n".join(f"{i+1}. {n}" for i, n in enumerate(_notes))


TOOLS = {"search_web": search_web, "calculator": calculator, "take_note": take_note, "read_notes": read_notes}

TOOL_SCHEMAS = [
    {"type": "function", "function": {"name": "search_web", "description": "Search the web.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "calculator", "description": "Evaluate math.", "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}}},
    {"type": "function", "function": {"name": "take_note", "description": "Save a note.", "parameters": {"type": "object", "properties": {"content": {"type": "string"}}, "required": ["content"]}}},
    {"type": "function", "function": {"name": "read_notes", "description": "Read all notes.", "parameters": {"type": "object", "properties": {}}}},
]


# ---------------------------------------------------------------------------
# Plan-and-Execute
# ---------------------------------------------------------------------------

@dataclass
class PlanStep:
    number: int
    description: str
    status: str = "pending"
    result: str = ""


def generate_plan(goal: str, client: OpenAI) -> list[PlanStep]:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a planning assistant. Given a goal, break it into 3-6 concrete steps. "
                    "Return JSON: {\"steps\": [{\"number\": 1, \"description\": \"...\"}]}. "
                    "Each step should be a single, actionable task that can use web search, "
                    "calculation, or note-taking tools."
                ),
            },
            {"role": "user", "content": goal},
        ],
    )
    data = json.loads(response.choices[0].message.content)
    return [PlanStep(number=s["number"], description=s["description"]) for s in data["steps"]]


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
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content or "(no result)"

        messages.append(msg)
        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)
            result = TOOLS[fn_name](**fn_args)
            messages.append({"role": "tool", "content": result, "tool_call_id": tc.id})

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

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "A step in a plan failed. Revise the remaining steps based on what happened. "
                    "Return JSON: {\"steps\": [{\"number\": N, \"description\": \"...\"}]}"
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
    data = json.loads(response.choices[0].message.content)
    start_num = len(completed) + 1
    return [
        PlanStep(number=start_num + i, description=s["description"])
        for i, s in enumerate(data["steps"])
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
                print(f"  Revised plan:")
                for s in plan[i:]:
                    print(f"    {s.number}. {s.description}")
                print()
            else:
                completed.append(step)
                i += 1

    synthesis_prompt = "\n".join(
        f"{s.number}. {s.description} -> {s.result}" for s in completed
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Synthesise the results of these steps into a final answer."},
            {"role": "user", "content": synthesis_prompt},
        ],
    )
    answer = response.choices[0].message.content
    return {"answer": answer, "plan": completed}


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def wait():
    input("\n--- Press Enter to continue ---\n")


def main():
    client = OpenAI()

    print("=" * 60)
    print("  MODULE 8 DEMO — Plan-and-Execute")
    print("=" * 60)

    print("\n## Plan-and-Execute Pattern\n")
    print("Instead of deciding one step at a time (ReAct),")
    print("we generate a FULL PLAN up front, then execute each step.\n")

    goals = [
        "Research the top 3 tallest buildings in the world, calculate the average height, and save the findings as a note.",
        "Find out the current population of Tokyo, compare it to London, and calculate the ratio.",
    ]

    for goal in goals:
        print(f"Goal: {goal}")
        result = plan_and_execute(goal, client)
        print(f"\n  Final Answer: {result['answer']}\n")
        wait()

    print("## Interactive — Try your own goals\n")
    print("Type a multi-step goal, or 'quit' to end.\n")

    while True:
        user_input = input("Goal: ").strip()
        if not user_input or user_input.lower() == "quit":
            break
        result = plan_and_execute(user_input, client)
        print(f"\nFinal Answer: {result['answer']}\n")

    print("Done.")


if __name__ == "__main__":
    main()
