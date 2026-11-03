"""Part 2: ReAct - a visible Thought, and the guards that stop a runaway loop.

Module 2 already built a tool-calling loop. ReAct is what you add on top: the
model must write down *why* before it acts, so the trace explains itself.

Asking for the reasoning as a structured field is what makes that reliable.
With native tool calling the assistant text is usually empty whenever the model
emits a call, so a "Thought" line you read off `output_text` mostly never
appears. Here the thought is a required field, so it cannot go missing.

Run alone:  python module-08-structured-workflows/demo/02_react.py
"""

from __future__ import annotations

from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from workflow_tools import MODEL, run_tool

load_dotenv()

# Every tool here takes a single string argument, so one `action_input` field
# covers them all and the response schema stays flat.
ARG_NAME = {
    "check_system": "system",
    "search_logs": "query",
    "lookup_mission": "mission_id",
    "calculator": "expression",
}

TOOL_MENU = """\
- check_system(system): one of reactor, navigation, life_support, shields, sensors
- search_logs(query): keyword search over the ship's logs
- lookup_mission(mission_id): look up a mission, e.g. MSN-001
- calculator(expression): evaluate arithmetic
- final_answer(text): finish and report"""


class ReActStep(BaseModel):
    """One turn of the loop. The thought is required, so it is always traced."""

    thought: str
    action: Literal[
        "check_system", "search_logs", "lookup_mission", "calculator", "final_answer"
    ]
    action_input: str


SYSTEM_PROMPT = (
    "You are the Pathfinder's duty officer, working one step at a time.\n"
    "On each turn: write your reasoning in `thought`, choose one `action`, and "
    "supply its single argument as `action_input`.\n"
    f"Available actions:\n{TOOL_MENU}\n"
    "Use final_answer as soon as you can answer. Do not repeat an action you "
    "have already taken - the observation will not change."
)


def _decide(messages: list[dict], client: OpenAI) -> ReActStep | None:
    response = client.responses.parse(
        model=MODEL,
        reasoning={"effort": "none"},
        text_format=ReActStep,
        input=messages,
    )
    return response.output_parsed


def run_react(query: str, client: OpenAI, max_steps: int = 6) -> dict:
    """ReAct with three guards: a step budget, no-progress detection, and a forced finish."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]
    trace: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for step in range(max_steps):
        decision = _decide(messages, client)
        if decision is None:
            trace.append({"type": "error", "content": "model refused to produce a step"})
            return {"answer": None, "trace": trace, "stop_reason": "refusal"}

        trace.append({"type": "thought", "content": decision.thought})

        if decision.action == "final_answer":
            trace.append({"type": "answer", "content": decision.action_input})
            return {"answer": decision.action_input, "trace": trace, "stop_reason": "answered"}

        signature = (decision.action, decision.action_input.strip().lower())
        if signature in seen:
            # Guard 2: the model is going in circles. Repeating a call burns a
            # step and returns an observation it has already seen, so say so
            # rather than letting it spin out the rest of the budget.
            trace.append({"type": "guard", "content": f"repeat of {decision.action}, nudging"})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"You already called {decision.action} with that input and the "
                        "result is above. Choose a different action or use final_answer."
                    ),
                }
            )
            continue
        seen.add(signature)

        trace.append(
            {"type": "action", "tool": decision.action, "input": decision.action_input}
        )
        observation = run_tool(decision.action, {ARG_NAME[decision.action]: decision.action_input})
        trace.append({"type": "observation", "content": observation})

        messages.append(
            {
                "role": "assistant",
                "content": (
                    f"Thought: {decision.thought}\n"
                    f"Action: {decision.action}({decision.action_input})"
                ),
            }
        )
        messages.append({"role": "user", "content": f"Observation: {observation}"})

    # Guard 3: the budget is gone. Do not return empty-handed - spend one more
    # call forcing an answer out of whatever was gathered.
    trace.append(
        {"type": "guard", "content": f"step budget of {max_steps} exhausted, forcing an answer"}
    )
    messages.append(
        {
            "role": "user",
            "content": "You are out of steps. Answer now with what you have, noting any gaps.",
        }
    )
    response = client.responses.create(model=MODEL, reasoning={"effort": "none"}, input=messages)
    answer = response.output_text
    trace.append({"type": "answer", "content": answer})
    return {"answer": answer, "trace": trace, "stop_reason": "budget_exhausted"}


def print_trace(trace: list[dict]) -> None:
    labels = {
        "thought": "Thought",
        "action": "Action ",
        "observation": "Observe",
        "answer": "Answer ",
        "guard": "GUARD  ",
        "error": "ERROR  ",
    }
    for entry in trace:
        label = labels.get(entry["type"], entry["type"])
        if entry["type"] == "action":
            body = f"{entry['tool']}({entry['input']})"
        else:
            body = " ".join(entry.get("content", "").split())[:160]
        print(f"    {label} | {body}")


# ---------------------------------------------------------------------------
# A model that will not stop, so the guard has something to catch
# ---------------------------------------------------------------------------

class _StuckClient:
    """Stand-in that always asks for the same tool, no API key needed."""

    class _Responses:
        def parse(self, **kwargs):
            class _R:
                output_parsed = ReActStep(
                    thought="I should check the shields.",
                    action="check_system",
                    action_input="shields",
                )

            return _R()

        def create(self, **kwargs):
            class _R:
                output_text = "Shields are at 85% and recharging. Unable to confirm the rest."

            return _R()

    responses = _Responses()


def demo_react(client: OpenAI):
    print("=" * 72)
    print("PART 2: REACT, WITH THE THOUGHT MADE VISIBLE")
    print("=" * 72)
    print()
    print("  The thought is a required field on the response schema.")
    print("  That is the difference between a trace that explains itself")
    print("  and the bare tool log you already built in Module 2.\n")

    query = (
        "Sensor maintenance needs a 2 hour downtime. Shields are recharging. "
        "Can we finish the maintenance before the shields reach full charge?"
    )
    print(f"  Query: {query}\n")
    result = run_react(query, client, max_steps=6)
    print_trace(result["trace"])
    print(f"\n    Stopped because: {result['stop_reason']}")
    print(f"    Answer: {result['answer']}\n")

    print("-" * 72)
    print("  Now the same loop against a model that will not stop.")
    print("  No API key needed - this one always asks for check_system(shields).\n")

    stuck = run_react("Status report", _StuckClient(), max_steps=4)
    print_trace(stuck["trace"])
    print(f"\n    Stopped because: {stuck['stop_reason']}")
    print()
    print("  Without the repeat guard this loop would have spent its whole")
    print("  budget on one tool. Without the forced finish it would have")
    print("  returned None. Both are a bad afternoon in production.")
    print()


if __name__ == "__main__":
    demo_react(OpenAI())
