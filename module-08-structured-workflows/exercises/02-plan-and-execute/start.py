"""
Exercise 02 — Plan-and-Execute
Separate planning from execution: LLM plans, ReAct executes each step.
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import OpenAI

from react_agent import run_react, TOOLS, print_trace

load_dotenv()


@dataclass
class PlanStep:
    step_number: int
    description: str
    status: str = "pending"
    result: str = ""


def generate_plan(query: str, client: OpenAI) -> list[PlanStep]:
    """Ask the LLM to create a numbered plan. Returns list of PlanStep."""
    # TODO: call client.chat.completions.create with:
    #   model="gpt-4o-mini"
    #   response_format={"type": "json_object"}
    #   A system prompt asking for a JSON object with a "steps" array
    #   Each step: {"step_number": int, "description": str}
    # Parse the JSON and return a list of PlanStep objects
    raise NotImplementedError("TODO")


def execute_step(
    step: PlanStep,
    previous_results: list[dict],
    client: OpenAI,
) -> dict:
    """Execute a single plan step using the ReAct agent. Returns result dict."""
    # TODO: build a query string that includes:
    #   - The step description
    #   - Context from previous results (so the agent knows what was already found)
    # Call run_react(query, client) and return the result
    raise NotImplementedError("TODO")


def revise_plan(
    plan: list[PlanStep],
    results: list[dict],
    original_query: str,
    client: OpenAI,
) -> list[PlanStep]:
    """Revise remaining plan steps after a failure. Returns new steps."""
    # TODO: call the LLM with context about:
    #   - The original query
    #   - Steps completed so far (with results)
    #   - Steps remaining
    # Ask it to return revised remaining steps as JSON
    # Parse and return as PlanStep list
    raise NotImplementedError("TODO")


def plan_and_execute(query: str, client: OpenAI) -> dict:
    """Full plan-and-execute loop. Returns {"answer": str, "plan": list[PlanStep]}."""
    # TODO: orchestrate the full workflow:
    # 1. Generate a plan with generate_plan()
    # 2. Print the plan
    # 3. For each step:
    #    a. Set status to "running" and print progress
    #    b. Call execute_step()
    #    c. On success: set status to "done", store result
    #    d. On failure: call revise_plan() to adjust remaining steps
    # 4. After all steps, compile the results into a final summary
    # 5. Return {"answer": final_answer, "plan": plan}
    raise NotImplementedError("TODO")


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
