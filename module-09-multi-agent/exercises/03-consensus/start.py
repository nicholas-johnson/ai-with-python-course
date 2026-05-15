"""
Exercise 03 — Debate + Consensus
Multiple resolution strategies: structured debate, consensus voting,
and a combined pipeline with supervisor validation.

Run:  python start.py
"""
from __future__ import annotations
import json
from collections import Counter
from openai import OpenAI

from agents import DEPARTMENTS, specialist_agent
from supervisor import run_supervised_query


def debate(question: str, client: OpenAI, rounds: int = 2) -> list[dict]:
    """Run a structured debate between an advocate and a skeptic.

    Returns a list of round dicts:
        [{"round": 1, "advocate": str, "skeptic": str}, ...]

    Steps:
        1. Set up message histories for advocate and skeptic with system prompts
           - Advocate: argues FOR the proposed action/idea
           - Skeptic: argues AGAINST, identifying risks and flaws
        2. For each round:
           a. Build the advocate's prompt (first round: the question;
              later rounds: the skeptic's last response)
           b. Call the LLM for the advocate and store the response
           c. Build the skeptic's prompt (includes the advocate's argument)
           d. Call the LLM for the skeptic and store the response
           e. Append {"round": N, "advocate": str, "skeptic": str} to the log
        3. Return the debate log
    """
    # TODO: implement structured debate
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
    # TODO: implement judge
    raise NotImplementedError("TODO")


def consensus_vote(question: str, client: OpenAI) -> dict:
    """Ask each specialist the same question and pick a winner by majority vote.

    Returns {
        "responses": [{"department": str, "response": str}, ...],
        "winner": str,
        "votes": {"navigation": int, "engineering": int, "science": int}
    }

    Steps:
        1. For each department in DEPARTMENTS, call specialist_agent
           and collect responses as [{"department": str, "response": str}, ...]
        2. Format all responses into a single text block
        3. For each department, ask a voting agent (LLM with JSON mode)
           which department gave the best answer
        4. Tally the votes and find the winner (highest count)
        5. Return the responses, winner, and vote counts
    """
    # TODO: implement consensus voting
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
    # TODO: implement multi-agent answer pipeline
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

        if user_input.startswith("/mode"):
            parts = user_input.split(maxsplit=1)
            if len(parts) == 2 and parts[1] in ("debate", "vote", "auto"):
                mode = parts[1]
                print(f"[Mode set to: {mode}]\n")
            else:
                print("[Usage: /mode debate|vote|auto]\n")
            continue

        if user_input.startswith("/debate "):
            question = user_input[8:].strip()
            if not question:
                print("[Provide a question to debate]\n")
                continue
            print("[Running debate...]")
            log = debate(question, client, rounds=2)
            for entry in log:
                print(f"\n  Round {entry['round']}:")
                print(f"    Advocate: {entry['advocate'][:120]}...")
                print(f"    Skeptic:  {entry['skeptic'][:120]}...")
            final = log[-1]
            judgment = judge(question, final["advocate"], final["skeptic"], client)
            print(f"\n  [Judge] Winner: {judgment['winner']}")
            print(f"  Reasoning: {judgment['reasoning']}\n")
            continue

        if user_input.startswith("/vote "):
            question = user_input[6:].strip()
            if not question:
                print("[Provide a question to vote on]\n")
                continue
            print("[Running consensus vote...]")
            result = consensus_vote(question, client)
            for entry in result["responses"]:
                print(f"  [{entry['department']}]: {entry['response'][:100]}...")
            print(f"\n  Votes: {result['votes']}")
            print(f"  Winner: {result['winner']}\n")
            continue

        if mode == "debate":
            print("[Running debate pipeline...]")
            result = multi_agent_answer(user_input, client)
            print(f"[Supervised answer from {result['supervised']['department']}]")
            print(f"  {result['supervised']['response'][:150]}...")
            print(f"[Debate judgment: {result['judgment']['winner']}]")
            print(f"  {result['judgment']['reasoning']}\n")
        elif mode == "vote":
            print("[Running consensus vote...]")
            result = consensus_vote(user_input, client)
            winning_response = next(
                r["response"]
                for r in result["responses"]
                if r["department"] == result["winner"]
            )
            print(f"[Winner: {result['winner']}] (votes: {result['votes']})")
            print(f"Agent: {winning_response}\n")
        else:
            print("[Running full multi-agent pipeline...]")
            result = multi_agent_answer(user_input, client)
            print(f"[Supervised: {result['supervised']['department']}]")
            print(f"  {result['supervised']['response'][:150]}...")
            print(f"[Debate judgment: {result['judgment']['winner']}]")
            print(f"  {result['judgment']['reasoning']}\n")


if __name__ == "__main__":
    main()
