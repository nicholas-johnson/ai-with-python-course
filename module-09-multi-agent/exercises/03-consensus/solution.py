"""
Exercise 03 — Debate + Consensus (solution)
Multiple resolution strategies: structured debate, consensus voting,
and a combined pipeline with supervisor validation.

Run:  python solution.py
"""
from __future__ import annotations
import json
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
    """Run one advocate turn. Appends to advocate_history. Returns the argument."""
    if round_num == 1:
        advocate_history.append({"role": "user", "content": f"Argue FOR: {question}"})
    else:
        advocate_history.append({
            "role": "user",
            "content": (
                f"The Skeptic responded: {last_skeptic_arg}\n\n"
                "Continue your argument."
            ),
        })

    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=advocate_history
    )
    arg = response.choices[0].message.content
    advocate_history.append({"role": "assistant", "content": arg})
    return arg


def _skeptic_turn(
    question: str,
    advocate_arg: str,
    skeptic_history: list[dict],
    round_num: int,
    client: OpenAI,
) -> str:
    """Run one skeptic turn. Appends to skeptic_history. Returns the argument."""
    if round_num == 1:
        skeptic_history.append({
            "role": "user",
            "content": (
                f"The question is: {question}\n\n"
                f"The Advocate argues: {advocate_arg}\n\n"
                "Argue AGAINST this position."
            ),
        })
    else:
        skeptic_history.append({
            "role": "user",
            "content": (
                f"The Advocate responded: {advocate_arg}\n\n"
                "Continue your counter-argument."
            ),
        })

    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=skeptic_history
    )
    arg = response.choices[0].message.content
    skeptic_history.append({"role": "assistant", "content": arg})
    return arg


def debate(question: str, client: OpenAI, rounds: int = 2) -> list[dict]:
    """Run a structured debate between an advocate and a skeptic.

    Returns a list of round dicts:
        [{"round": 1, "advocate": str, "skeptic": str}, ...]
    """
    advocate_history: list[dict] = [
        {
            "role": "system",
            "content": (
                "You are the Advocate aboard the DSS Pathfinder. "
                "Argue FOR the proposed action or idea. Be persuasive, "
                "cite potential benefits, and counter any objections raised."
            ),
        },
    ]
    skeptic_history: list[dict] = [
        {
            "role": "system",
            "content": (
                "You are the Skeptic aboard the DSS Pathfinder. "
                "Argue AGAINST the proposed action or idea. Identify risks, "
                "flaws, and unintended consequences. Be rigorous and specific."
            ),
        },
    ]

    debate_log: list[dict] = []

    for r in range(1, rounds + 1):
        last_skeptic = debate_log[-1]["skeptic"] if debate_log else None
        adv_arg = _advocate_turn(question, advocate_history, last_skeptic, r, client)
        skp_arg = _skeptic_turn(question, adv_arg, skeptic_history, r, client)
        debate_log.append({"round": r, "advocate": adv_arg, "skeptic": skp_arg})

    return debate_log


def judge(
    question: str, advocate_arg: str, skeptic_arg: str, client: OpenAI
) -> dict:
    """An LLM judge reviews both final positions and picks a winner.

    Returns {"winner": "advocate"|"skeptic", "reasoning": str}.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an impartial Judge aboard the DSS Pathfinder. "
                    "Review both arguments and decide which side made the "
                    "stronger case. Return JSON: "
                    '{"winner": "advocate" or "skeptic", "reasoning": "..."}.'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Advocate's final argument:\n{advocate_arg}\n\n"
                    f"Skeptic's final argument:\n{skeptic_arg}\n\n"
                    "Who made the stronger case?"
                ),
            },
        ],
    )
    try:
        data = json.loads(response.choices[0].message.content)
        winner = data.get("winner", "advocate").lower().strip()
        if winner not in ("advocate", "skeptic"):
            winner = "advocate"
        return {"winner": winner, "reasoning": str(data.get("reasoning", ""))}
    except (json.JSONDecodeError, AttributeError):
        return {"winner": "advocate", "reasoning": "Unable to parse judgment."}


def _collect_department_votes(
    question: str, responses: list[dict], client: OpenAI
) -> dict[str, int]:
    """Have each department vote on the best response. Returns vote tallies."""
    formatted = "\n".join(
        f"- {entry['department']}: {entry['response']}" for entry in responses
    )
    votes: dict[str, int] = {dept: 0 for dept in DEPARTMENTS}

    for dept in DEPARTMENTS:
        vote_result = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a voting agent. Given multiple specialist responses "
                        "to a question, pick the department that gave the BEST answer. "
                        'Return JSON: {"vote": "<department_name>"}. '
                        f"Valid departments: {', '.join(DEPARTMENTS)}."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Question: {question}\n\nResponses:\n{formatted}\n\n"
                        "Which department gave the best answer?"
                    ),
                },
            ],
        )
        try:
            data = json.loads(vote_result.choices[0].message.content)
            voted = data.get("vote", "").lower().strip()
            if voted in DEPARTMENTS:
                votes[voted] += 1
        except (json.JSONDecodeError, AttributeError):
            pass

    return votes


def consensus_vote(question: str, client: OpenAI) -> dict:
    """Ask each specialist the same question and pick a winner by majority vote.

    Returns {
        "responses": [{"department": str, "response": str}, ...],
        "winner": str,
        "votes": {"medical": int, "tactical": int, "comms": int}
    }
    """
    responses = []
    for dept in DEPARTMENTS:
        answer = specialist_agent(dept, question, client)
        responses.append({"department": dept, "response": answer})

    votes = _collect_department_votes(question, responses, client)
    winner = max(votes, key=lambda d: votes[d])
    return {"responses": responses, "winner": winner, "votes": votes}


def multi_agent_answer(
    query: str, client: OpenAI, max_revisions: int = 2
) -> dict:
    """Combine the supervisor pipeline with debate for validation.

    Returns {
        "supervised": dict (from run_supervised_query),
        "debate": list (debate rounds),
        "judgment": dict (from judge),
    }
    """
    supervised = run_supervised_query(query, client, max_revisions=max_revisions)

    debate_question = (
        f"Regarding '{query}', the specialist responded: "
        f"'{supervised['response']}'. Is this a good answer?"
    )
    debate_log = debate(debate_question, client, rounds=2)

    final_advocate = debate_log[-1]["advocate"]
    final_skeptic = debate_log[-1]["skeptic"]
    judgment = judge(debate_question, final_advocate, final_skeptic, client)

    return {
        "supervised": supervised,
        "debate": debate_log,
        "judgment": judgment,
    }


def handle_repl_command(user_input: str, mode: str, client: OpenAI) -> str:
    """Process one REPL command or query. Returns the (possibly updated) mode."""
    if user_input.startswith("/mode"):
        parts = user_input.split(maxsplit=1)
        if len(parts) == 2 and parts[1] in ("debate", "vote", "auto"):
            mode = parts[1]
            print(f"[Mode set to: {mode}]\n")
        else:
            print("[Usage: /mode debate|vote|auto]\n")
        return mode

    if user_input.startswith("/debate "):
        question = user_input[8:].strip()
        if not question:
            print("[Provide a question to debate]\n")
            return mode
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
        return mode

    if user_input.startswith("/vote "):
        question = user_input[6:].strip()
        if not question:
            print("[Provide a question to vote on]\n")
            return mode
        print("[Running consensus vote...]")
        result = consensus_vote(question, client)
        for entry in result["responses"]:
            print(f"  [{entry['department']}]: {entry['response'][:100]}...")
        print(f"\n  Votes: {result['votes']}")
        print(f"  Winner: {result['winner']}\n")
        return mode

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

    return mode


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
