"""
Exercise 04 — Swarm Agents with Scoped Tools

Agents hand off peer-to-peer; each has scoped mock ship tools.

Run:  python start.py
"""
from __future__ import annotations

import json
from dotenv import load_dotenv
from openai import OpenAI

from tools import AGENT_PROMPTS, AGENT_TOOLS, DEPARTMENTS, TOOL_FUNCTIONS

load_dotenv()

MODEL = "gpt-4o-mini"


def build_agent_messages(department: str, query: str) -> list[dict]:
    """Initial message list for an agent turn.

    Steps:
        1. Look up AGENT_PROMPTS[department] (fallback to comms)
        2. Return system + user messages with the query
    """
    # TODO: implement
    raise NotImplementedError("TODO")


def run_agent_turn(department: str, messages: list[dict], client: OpenAI):
    """One LLM call with the agent's scoped tools.

    Steps:
        1. Get tools from AGENT_TOOLS[department]
        2. Call client.chat.completions.create with model, messages, tools, tool_choice="auto"
        3. Return response.choices[0].message
    """
    # TODO: implement
    raise NotImplementedError("TODO")


def handle_tool_calls(response_message, department: str) -> tuple[list[dict], str | None]:
    """Execute tool calls; detect transfer_to_* handoffs.

    Returns:
        (tool_messages, transfer_target)

    Steps:
        1. If no tool_calls, return ([], None)
        2. Build assistant message dict with tool_calls list
        3. For each tool_call: parse args, invoke TOOL_FUNCTIONS, append tool message
        4. If transfer tool, parse JSON for transfer_to and set transfer_target
    """
    # TODO: implement
    raise NotImplementedError("TODO")


def swarm_loop(
    query: str,
    client: OpenAI,
    start_dept: str = "comms",
    max_hops: int = 6,
) -> dict:
    """Run swarm until final text answer or max_hops.

    Returns:
        {"answer": str, "chain": list[str], "trace": list[dict]}

    Steps:
        1. Initialise department, messages, chain, trace
        2. Loop up to max_hops: run_agent_turn, handle tools or return answer
        3. On handoff, switch department and append a short user nudge message
    """
    # TODO: implement
    raise NotImplementedError("TODO")


def main():
    client = OpenAI()
    start_dept = "comms"
    max_hops = 6

    print("=" * 60)
    print("  MODULE 9 — Swarm Agents with Scoped Tools")
    print("  DSS Pathfinder Multi-Agent System")
    print("=" * 60)
    print("Commands: /start <dept>, /trace, /hops N, /agents, quit\n")

    last_result = None

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input == "/agents":
            print("[Swarm agents]")
            for dept in DEPARTMENTS:
                names = [t["function"]["name"] for t in AGENT_TOOLS[dept]]
                print(f"  {dept}: {', '.join(names)}")
            print()
            continue

        if user_input.startswith("/start "):
            dept = user_input[7:].strip().lower()
            if dept in DEPARTMENTS:
                start_dept = dept
                print(f"[Start agent set to: {start_dept}]\n")
            else:
                print(f"[Valid: {', '.join(DEPARTMENTS)}]\n")
            continue

        if user_input.startswith("/hops "):
            parts = user_input.split()
            if len(parts) == 2 and parts[1].isdigit():
                max_hops = int(parts[1])
                print(f"[Max hops set to {max_hops}]\n")
            else:
                print("[Usage: /hops N]\n")
            continue

        if user_input == "/trace":
            if last_result is None:
                print("[No trace yet — ask a question first]\n")
            else:
                print("[Swarm trace]")
                for step in last_result["trace"]:
                    print(f"  {step}")
                print(f"  Chain: {' -> '.join(last_result['chain'])}\n")
            continue

        print("[Running swarm...]")
        last_result = swarm_loop(user_input, client, start_dept=start_dept, max_hops=max_hops)
        chain_str = " -> ".join(last_result["chain"])
        print(f"[Chain: {chain_str}]")
        print(f"Agent: {last_result['answer']}\n")


if __name__ == "__main__":
    main()
