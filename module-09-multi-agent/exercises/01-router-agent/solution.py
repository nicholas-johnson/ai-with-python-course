"""
Exercise 01 — Router + Specialist Agents (solution)
Build specialist agents with focused system prompts, then route
user queries to the right specialist using LLM-based classification.

Run:  python solution.py
"""
from __future__ import annotations
import json
from openai import OpenAI

DEPARTMENTS = ["navigation", "engineering", "science"]

SPECIALIST_PROMPTS = {
    "navigation": (
        "You are the Navigation Officer aboard the DSS Pathfinder. "
        "You handle all questions about course headings, star charts, "
        "jump calculations, orbital mechanics, and positioning. "
        "Answer concisely and with authority."
    ),
    "engineering": (
        "You are the Chief Engineer aboard the DSS Pathfinder. "
        "You handle all questions about engines, hull integrity, "
        "power systems, shields, life support, and repairs. "
        "Answer concisely with technical precision."
    ),
    "science": (
        "You are the Science Officer aboard the DSS Pathfinder. "
        "You handle all questions about anomalies, sensor readings, "
        "nebula analysis, xenobiology, and research findings. "
        "Answer concisely and cite data where possible."
    ),
}


def classify_query(query: str, client: OpenAI) -> str:
    """Use the LLM to classify a query into a department.

    Returns one of: 'navigation', 'engineering', 'science'.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a query router for a starship crew. "
                    "Classify the user's message into exactly one department. "
                    'Return JSON: {"department": "<name>"}. '
                    "Valid departments: navigation, engineering, science. "
                    "navigation = headings, courses, star charts, positioning. "
                    "engineering = engines, hull, power, shields, repairs. "
                    "science = anomalies, sensors, nebulae, biology, research. "
                    "If unsure, pick the closest match."
                ),
            },
            {"role": "user", "content": query},
        ],
    )
    try:
        data = json.loads(response.choices[0].message.content)
        dept = data.get("department", "science").lower().strip()
        return dept if dept in DEPARTMENTS else "science"
    except (json.JSONDecodeError, AttributeError):
        return "science"


def specialist_agent(department: str, query: str, client: OpenAI) -> str:
    """Run a specialist agent for the given department."""
    system_prompt = SPECIALIST_PROMPTS.get(department, SPECIALIST_PROMPTS["science"])
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
    )
    return response.choices[0].message.content


def route_and_respond(query: str, client: OpenAI) -> dict:
    """Classify a query, dispatch to the right specialist, return the result.

    Returns:
        {"department": str, "response": str}
    """
    department = classify_query(query, client)
    response = specialist_agent(department, query, client)
    return {"department": department, "response": response}


def main():
    client = OpenAI()

    print("=" * 60)
    print("  MODULE 9 — Router + Specialist Agents")
    print("  DSS Pathfinder Multi-Agent System")
    print("=" * 60)
    print("Commands: /route <msg>, /specialists, quit\n")

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

        if user_input == "/specialists":
            print("[Available specialist agents]")
            for dept, prompt in SPECIALIST_PROMPTS.items():
                print(f"  {dept}: {prompt[:60]}...")
            print()
            continue

        if user_input.startswith("/route "):
            msg = user_input[7:].strip()
            if not msg:
                print("[Provide a message to classify]\n")
                continue
            dept = classify_query(msg, client)
            print(f"[Router] → {dept}\n")
            continue

        result = route_and_respond(user_input, client)
        print(f"[Routed to: {result['department']}]")
        print(f"Agent: {result['response']}\n")


if __name__ == "__main__":
    main()
