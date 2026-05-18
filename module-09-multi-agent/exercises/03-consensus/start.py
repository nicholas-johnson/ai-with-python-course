"""
Exercise 03 — Debate + Consensus
Multiple resolution strategies: structured debate, consensus voting,
and a combined pipeline with supervisor validation.

Run:  python start.py
"""
from __future__ import annotations
from dotenv import load_dotenv
from openai import OpenAI

from agents import DEPARTMENTS, specialist_agent
from supervisor import run_supervised_query

load_dotenv()


def _advocate_turn(
    question: str,
    advocate_history: list[dict],
    last_skeptic_arg: str | None,
    round_num: int,
    client: OpenAI,
) -> str:
    """Run one advocate turn. Appends to advocate_history. Returns the argument.

    - Round 1: prompt with the question itself
    - Later rounds: prompt with the skeptic's last response
    Then call the LLM, append the assistant reply, and return it.
    """
    # TODO: implement
    raise NotImplementedError("TODO")


def _skeptic_turn(
    question: str,
    advocate_arg: str,
    skeptic_history: list[dict],
    round_num: int,
    client: OpenAI,
) -> str:
    """Run one skeptic turn. Appends to skeptic_history. Returns the argument.

    - Round 1: prompt with the question and the advocate's argument
    - Later rounds: prompt with the advocate's latest response
    Then call the LLM, append the assistant reply, and return it.
    """
    # TODO: implement
    raise NotImplementedError("TODO")


def debate(question: str, client: OpenAI, rounds: int = 2) -> list[dict]:
    """Run a structured debate between an advocate and a skeptic.

    Returns a list of round dicts:
        [{"round": 1, "advocate": str, "skeptic": str}, ...]

    Steps:
        1. Set up advocate_history and skeptic_history with system prompts
        2. For each round, call _advocate_turn then _skeptic_turn
        3. Append {"round": N, "advocate": str, "skeptic": str} to the log
    """
    # TODO: implement
    raise NotImplementedError("TODO")


def judge(
    question: str, advocate_arg: str, skeptic_arg: str, client: OpenAI
) -> dict:
    """An LLM judge reviews both final positions and picks a winner.

    Returns {"winner": "advocate"|"skeptic", "reasoning": str}.

    Steps:
        1. Call the LLM with response_format={"type": "json_object"}
        2. System prompt: impartial judge, pick the stronger argument
        3. User prompt: include the question and both final arguments
        4. Parse JSON response for "winner" and "reasoning"
        5. Default to "advocate" if parsing fails or winner is invalid
    """
    # TODO: implement
    raise NotImplementedError("TODO")


def _collect_department_votes(
    question: str, responses: list[dict], client: OpenAI
) -> dict[str, int]:
    """Have each department vote on the best response. Returns vote tallies.

    Steps:
        1. Format all responses into a single text block
        2. For each department, ask a voting agent (LLM with JSON mode)
           which department gave the best answer
        3. Tally valid votes and return {dept: count, ...}
    """
    # TODO: implement
    raise NotImplementedError("TODO")


def consensus_vote(question: str, client: OpenAI) -> dict:
    """Ask each specialist the same question and pick a winner by majority vote.

    Returns {
        "responses": [{"department": str, "response": str}, ...],
        "winner": str,
        "votes": {"navigation": int, "engineering": int, "science": int}
    }

    Steps:
        1. For each department, call specialist_agent and collect responses
        2. Call _collect_department_votes to tally votes
        3. Find the winner (highest vote count)
    """
    # TODO: implement
    raise NotImplementedError("TODO")


def multi_agent_answer(
    query: str, client: OpenAI, max_revisions: int = 2
) -> dict:
    """Combine the supervisor pipeline with debate for validation.

    Returns {
        "supervised": dict (from run_supervised_query),
        "debate": list (debate rounds),
        "judgment": dict (from judge),
    }

    Steps:
        1. Call run_supervised_query to get the supervised answer
        2. Construct a debate question around the supervised response
        3. Run debate() on that question
        4. Extract the final advocate and skeptic arguments
        5. Call judge() to pick a winner
        6. Return all three results combined
    """
    # TODO: implement
    raise NotImplementedError("TODO")


def handle_repl_command(user_input: str, mode: str, client: OpenAI) -> str:
    """Process one REPL command or query. Returns the (possibly updated) mode.

    Slash commands:
        /mode <debate|vote|auto> — switch mode
        /debate <question> — run a standalone debate + judge
        /vote <question> — run a standalone consensus vote

    Default (no slash): dispatch based on current mode.
    """
    # TODO: implement
    raise NotImplementedError("TODO")


def main():
    client = OpenAI()
    mode = "auto"

    print("=" * 60)
    print("  MODULE 9 — Debate + Consensus")
    print("  DSS Pathfinder Multi-Agent System")
    print("=" * 60)
    print("Commands: /debate <q>, /vote <q>, /mode debate|vote|auto, quit\n")

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

        mode = handle_repl_command(user_input, mode, client)


if __name__ == "__main__":
    main()
