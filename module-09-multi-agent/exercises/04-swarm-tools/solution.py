"""
Exercise 04 — Swarm Agents with Scoped Tools (solution)

Agents hand off peer-to-peer; each has scoped mock ship tools.

Run:  python solution.py
"""
from __future__ import annotations

import json
import os
from dotenv import load_dotenv
from openai import OpenAI

from tools import AGENT_PROMPTS, AGENT_TOOLS, DEPARTMENTS, TOOL_FUNCTIONS

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


def build_agent_messages(department: str, query: str) -> list[dict]:
    """Initial message list for an agent turn."""
    prompt = AGENT_PROMPTS.get(department, AGENT_PROMPTS["comms"])
    return [
        {"role": "system", "content": prompt},
        {"role": "user", "content": query},
    ]


def run_agent_turn(department: str, messages: list[dict], client: OpenAI):
    """One LLM call with the agent's scoped tools."""
    tools = AGENT_TOOLS.get(department, AGENT_TOOLS["comms"])
    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=messages,
        tools=tools,
        tool_choice="auto",
    )
    return response


def function_calls(response) -> list:
    """The function_call items in a response's output (empty if the model answered)."""
    return [item for item in response.output if item.type == "function_call"]


def handle_tool_calls(response, department: str) -> tuple[list, str | None]:
    """
    Execute the function calls in the agent's response.

    Returns:
        (new_items, transfer_target)
        new_items is the model's output followed by one function_call_output per call,
        ready to extend the conversation. transfer_target is set when a
        transfer_to_* tool was called.
    """
    calls = function_calls(response)
    transfer_target: str | None = None

    if not calls:
        return [], transfer_target

    # Keep the model's function_call items so each output can be matched by call_id
    tool_messages: list = list(response.output)

    for tc in calls:
        fn_name = tc.name
        try:
            fn_args = json.loads(tc.arguments or "{}")
        except json.JSONDecodeError:
            fn_args = {}

        if fn_name.startswith("transfer_to_"):
            result = TOOL_FUNCTIONS[fn_name]()
            try:
                data = json.loads(result)
                transfer_target = data.get("transfer_to")
            except json.JSONDecodeError:
                transfer_target = fn_name.replace("transfer_to_", "")
        elif fn_name in TOOL_FUNCTIONS:
            result = TOOL_FUNCTIONS[fn_name](**fn_args)
        else:
            result = f"Unknown tool: {fn_name}"

        tool_messages.append(
            {
                "type": "function_call_output",
                "call_id": tc.call_id,
                "output": result if isinstance(result, str) else json.dumps(result),
            }
        )

    return tool_messages, transfer_target


def swarm_loop(
    query: str,
    client: OpenAI,
    start_dept: str = "comms",
    max_hops: int = 6,
) -> dict:
    """
    Run the swarm until a final text answer or max_hops.

    Returns:
        {
            "answer": str,
            "chain": list[str],  # departments visited
            "trace": list[dict],
        }
    """
    if start_dept not in DEPARTMENTS:
        start_dept = "comms"

    department = start_dept
    messages = build_agent_messages(department, query)
    chain: list[str] = [department]
    trace: list[dict] = []

    for hop in range(max_hops):
        trace.append({"hop": hop + 1, "agent": department, "action": "llm_turn"})
        response = run_agent_turn(department, messages, client)

        if not function_calls(response):
            answer = response.output_text
            trace.append({"hop": hop + 1, "agent": department, "action": "final_answer"})
            return {"answer": answer, "chain": chain, "trace": trace}

        tool_msgs, transfer = handle_tool_calls(response, department)
        messages.extend(tool_msgs)

        for tm in tool_msgs:
            if isinstance(tm, dict) and tm.get("type") == "function_call_output":
                trace.append(
                    {
                        "hop": hop + 1,
                        "agent": department,
                        "action": "tool_result",
                        "content": tm.get("output", "")[:120],
                    }
                )

        if transfer and transfer in DEPARTMENTS and transfer != department:
            trace.append({"hop": hop + 1, "agent": department, "action": "handoff", "to": transfer})
            department = transfer
            chain.append(department)
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"You are now the active officer ({department}). "
                        "Continue helping the crew using your tools. "
                        "Summarise for the user when done."
                    ),
                }
            )
            continue

        # More tool rounds on same agent
        trace.append({"hop": hop + 1, "agent": department, "action": "continue_tools"})

    return {
        "answer": "(max hops reached — try a simpler query or raise max_hops)",
        "chain": chain,
        "trace": trace,
    }


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
                names = [t["name"] for t in AGENT_TOOLS[dept]]
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
