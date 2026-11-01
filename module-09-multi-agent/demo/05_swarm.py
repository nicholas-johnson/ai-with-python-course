"""Part 5: Agents hand off to each other, each with their own tools."""

import sys
from pathlib import Path

from openai import OpenAI

_EX04 = Path(__file__).resolve().parent.parent / "exercises" / "04-swarm-tools"
if str(_EX04) not in sys.path:
    sys.path.insert(0, str(_EX04))
from solution import swarm_loop  # noqa: E402


def demo_swarm(client: OpenAI):
    print("=" * 60)
    print("PART 5: SWARM")
    print("=" * 60)
    print()

    query = (
        "Decrypt incoming signal X42 and check if the reactor can handle "
        "a power boost to amplify the relay array."
    )
    print(f"  Query: {query}")
    print("  Start: comms\n")

    result = swarm_loop(query, client, start_dept="comms", max_hops=8)
    print("\n  [Swarm trace]")
    for step in result["trace"]:
        action = step.get("action", "")
        agent = step.get("agent", "")
        if action == "handoff":
            print(f"    {agent} --handoff--> {step.get('to')}")
        elif action == "tool_result":
            preview = step.get("content", "")[:80]
            print(f"    {agent} tool: {preview}...")
        elif action == "final_answer":
            print(f"    {agent} final answer")
        else:
            print(f"    {agent}: {action}")

    chain = " -> ".join(result["chain"])
    print(f"\n  Chain:  {chain} -> (done)")
    print(f"  Answer: {result['answer']}\n")
