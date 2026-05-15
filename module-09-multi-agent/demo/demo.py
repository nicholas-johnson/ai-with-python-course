"""
MODULE 9 DEMO — Multi-Agent Systems

Interactive walkthrough of specialist routing, supervisor-critic
pipelines, structured debate, and consensus voting aboard the
DSS Pathfinder.

Run:  python module-09-multi-agent/demo/demo.py
"""
from __future__ import annotations

import json
from openai import OpenAI

MODEL = "gpt-4o-mini"

SPECIALIST_PROMPTS = {
    "navigation": (
        "You are the Navigation Officer aboard the DSS Pathfinder. "
        "You handle course plotting, stellar cartography, speed and heading, "
        "and hazard avoidance. Answer concisely in 2-3 sentences."
    ),
    "engineering": (
        "You are the Chief Engineer aboard the DSS Pathfinder. "
        "You handle reactor output, hull integrity, shields, and ship systems. "
        "Answer concisely in 2-3 sentences."
    ),
    "science": (
        "You are the Science Officer aboard the DSS Pathfinder. "
        "You handle sensor analysis, anomaly research, planetary surveys, "
        "and xenobiology. Answer concisely in 2-3 sentences."
    ),
}

DEPARTMENTS = list(SPECIALIST_PROMPTS.keys())

def classify_query(query: str, client: OpenAI) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    f"Classify the user query into exactly one department: "
                    f"{', '.join(DEPARTMENTS)}. "
                    'Return JSON: {"department": "<name>"}'
                ),
            },
            {"role": "user", "content": query},
        ],
    )
    try:
        dept = json.loads(response.choices[0].message.content)["department"]
        return dept if dept in DEPARTMENTS else "science"
    except (json.JSONDecodeError, KeyError):
        return "science"

def specialist_respond(department: str, query: str, client: OpenAI) -> str:
    prompt = SPECIALIST_PROMPTS.get(department, SPECIALIST_PROMPTS["science"])
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": query},
        ],
    )
    return response.choices[0].message.content

def critic_review(query: str, answer: str, client: OpenAI) -> dict:
    """Returns {"approved": bool, "feedback": str}."""
    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior reviewer aboard the DSS Pathfinder. "
                    "Evaluate the specialist's answer for accuracy, completeness, "
                    "and safety. Return JSON: "
                    '{"approved": true/false, "feedback": "your feedback"}. '
                    "Only reject if the answer is clearly wrong, dangerous, or incomplete."
                ),
            },
            {
                "role": "user",
                "content": f"QUERY: {query}\n\nSPECIALIST ANSWER: {answer}",
            },
        ],
    )
    try:
        return json.loads(response.choices[0].message.content)
    except (json.JSONDecodeError, KeyError):
        return {"approved": True, "feedback": "Unable to parse review."}

def revise_answer(department: str, query: str, previous: str, feedback: str, client: OpenAI) -> str:
    prompt = SPECIALIST_PROMPTS.get(department, SPECIALIST_PROMPTS["science"])
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": query},
            {"role": "assistant", "content": previous},
            {"role": "user", "content": f"A reviewer rejected your answer: {feedback}\nPlease revise."},
        ],
    )
    return response.choices[0].message.content

def debate_round(topic: str, position: str, opponent_arg: str, client: OpenAI) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                f"You are a debate participant on the DSS Pathfinder. "
                f"Argue the '{position}' position on the given topic. "
                f"Be concise (2-3 sentences). If the opponent made an argument, "
                f"address it directly before making your own point."
            ),
        },
        {"role": "user", "content": f"Topic: {topic}"},
    ]
    if opponent_arg:
        messages.append({"role": "user", "content": f"Opponent's argument: {opponent_arg}"})
    response = client.chat.completions.create(model=MODEL, messages=messages)
    return response.choices[0].message.content

def judge_debate(topic: str, advocate_args: list[str], skeptic_args: list[str], client: OpenAI) -> str:
    transcript = ""
    for i, (a, s) in enumerate(zip(advocate_args, skeptic_args), 1):
        transcript += f"Round {i} — Advocate: {a}\nRound {i} — Skeptic: {s}\n\n"
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the Captain of the DSS Pathfinder acting as judge. "
                    "Read the debate transcript, weigh both sides, then declare "
                    "a winner (advocate or skeptic) with a brief rationale. "
                    "Keep your ruling to 3-4 sentences."
                ),
            },
            {"role": "user", "content": f"Topic: {topic}\n\n{transcript}"},
        ],
    )
    return response.choices[0].message.content

def wait():
    input("\n--- Press Enter to continue ---\n")

def main():
    client = OpenAI()

    print("=" * 60)
    print("  MODULE 9 DEMO — Multi-Agent Systems")
    print("=" * 60)

    # ---- Part 1: Specialist Agents + Router ----
    print("\n## Part 1: Specialist Agents + Router\n")
    print("An LLM classifies each query and routes it to the")
    print("right specialist agent (navigation, engineering, science).\n")

    test_queries = [
        "What is our current heading and ETA to Kepler-442b?",
        "Give me a hull integrity report after the ion storm.",
        "Analyse the unusual readings from the nearby nebula.",
    ]
    for query in test_queries:
        dept = classify_query(query, client)
        print(f"  Query:      {query}")
        print(f"  Routed to:  {dept}")
        response = specialist_respond(dept, query, client)
        print(f"  Response:   {response}\n")

    wait()

    # ---- Part 2: Supervisor-Critic Pipeline ----
    print("## Part 2: Supervisor-Critic Pipeline\n")
    print("A query goes through: router -> specialist -> critic.")
    print("If the critic rejects, the specialist revises.\n")

    query = "What's the safest route through the asteroid field at sector 7G?"
    dept = classify_query(query, client)
    answer = specialist_respond(dept, query, client)
    print(f"  Query:       {query}")
    print(f"  Routed to:   {dept}")
    print(f"  Draft:       {answer}\n")

    for attempt in range(1, 3):
        review = critic_review(query, answer, client)
        approved = review.get("approved", True)
        feedback = review.get("feedback", "")
        print(f"  Critic #{attempt}: {'APPROVED' if approved else 'REJECTED'}")
        print(f"  Feedback:    {feedback}\n")
        if approved:
            break
        answer = revise_answer(dept, query, answer, feedback, client)
        print(f"  Revision:    {answer}\n")

    print(f"  Final answer: {answer}")

    wait()

    # ---- Part 3: Debate ----
    print("## Part 3: Debate\n")
    print("Two agents debate a Pathfinder dilemma. A judge picks a winner.\n")

    topic = "Should the DSS Pathfinder divert through the asteroid field to save 3 days of travel time?"
    print(f"  Topic: {topic}\n")

    advocate_args: list[str] = []
    skeptic_args: list[str] = []

    for round_num in range(1, 3):
        print(f"  --- Round {round_num} ---")
        prev_skeptic = skeptic_args[-1] if skeptic_args else ""
        adv = debate_round(topic, "advocate — in favour of diverting", prev_skeptic, client)
        advocate_args.append(adv)
        print(f"  Advocate: {adv}\n")

        skp = debate_round(topic, "skeptic — against diverting", adv, client)
        skeptic_args.append(skp)
        print(f"  Skeptic:  {skp}\n")

    ruling = judge_debate(topic, advocate_args, skeptic_args, client)
    print(f"  Judge's ruling: {ruling}")

    wait()

    # ---- Part 4: Consensus Voting ----
    print("## Part 4: Consensus Voting\n")
    print("All three specialists answer the same question independently.")
    print("We tally votes to find the consensus.\n")

    question = "Should we reroute to avoid the ion storm, or maintain course and reinforce shields?"
    options = ["reroute", "maintain course"]
    print(f"  Question: {question}")
    print(f"  Options:  {options}\n")

    votes: dict[str, str] = {}
    for dept in DEPARTMENTS:
        response = client.chat.completions.create(
            model=MODEL,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"{SPECIALIST_PROMPTS[dept]} "
                        f"You must vote on the best course of action. "
                        f'Return JSON: {{"vote": "<option>", "reasoning": "brief rationale"}} '
                        f"where option is one of: {', '.join(options)}."
                    ),
                },
                {"role": "user", "content": question},
            ],
        )
        try:
            data = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            data = {"vote": options[0], "reasoning": "Parse error — defaulted."}
        vote = data.get("vote", options[0])
        reasoning = data.get("reasoning", "")
        votes[dept] = vote
        print(f"  {dept:>12}:  {vote}")
        print(f"               {reasoning}\n")

    tally: dict[str, int] = {}
    for v in votes.values():
        tally[v] = tally.get(v, 0) + 1

    winner = max(tally, key=tally.get)
    print(f"  Tally:   {tally}")
    print(f"  Winner:  {winner}")

    print("\n" + "=" * 60)
    print("  Demo complete.")
    print("=" * 60)

if __name__ == "__main__":
    main()
