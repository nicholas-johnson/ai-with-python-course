"""
Module 8 Demo — Structured Workflows
Run:  python module-08-structured-workflows/demo/demo.py

  Part 1: One task, four strategies - who owns the control flow
  Part 2: ReAct with a visible thought, and guards against a runaway loop
  Part 3: Plan-and-execute, with re-planning on failure
  Part 4: The plan is a graph - run independent steps concurrently
  Part 5: Pause for human approval, checkpoint, resume

Requires: OPENAI_API_KEY environment variable.
"""

from importlib import import_module

from dotenv import load_dotenv
from openai import OpenAI

demo_control_flow = import_module("01_control_flow").demo_control_flow
demo_react = import_module("02_react").demo_react
demo_plan_and_execute = import_module("03_plan_and_execute").demo_plan_and_execute
demo_parallel_plan = import_module("04_parallel_plan").demo_parallel_plan
demo_approval_resume = import_module("05_approval_resume").demo_approval_resume

DEMOS = {
    "1": ("Who owns the control flow", demo_control_flow),
    "2": ("ReAct and its guards", demo_react),
    "3": ("Plan-and-execute", demo_plan_and_execute),
    "4": ("Parallel plans", demo_parallel_plan),
    "5": ("Approval and resume", demo_approval_resume),
}


def main():
    load_dotenv()
    client = OpenAI()

    print("\n" + "=" * 72)
    print("  MODULE 8 DEMO — STRUCTURED WORKFLOWS")
    print("=" * 72)

    while True:
        print("\nPick a section:\n")
        for key, (label, _) in DEMOS.items():
            print(f"  {key}. {label}")
        print("  q. Quit\n")

        try:
            choice = input("Enter choice> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice in ("q", "quit", ""):
            break
        elif choice in DEMOS:
            _, fn = DEMOS[choice]
            print()
            fn(client)
        else:
            print(f"Unknown option: {choice}")

    print("\n" + "=" * 72)
    print("  RECAP")
    print("=" * 72)
    print()
    print("  1. Control flow — chain, router, plan, ReAct: a spectrum, not a choice of two")
    print("  2. ReAct        — the thought is a required field; cap the loop and catch repeats")
    print("  3. Plan         — decide once up front, and the plan becomes data you can show")
    print("  4. Parallel     — depends_on turns the plan into a graph you can schedule")
    print("  5. Approval     — a plan on disk can block on a human and survive a restart")
    print()
    print("  Push control flow as far left as the task allows.")
    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
