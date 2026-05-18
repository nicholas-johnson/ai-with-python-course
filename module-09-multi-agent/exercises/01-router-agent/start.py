"""
Exercise 01 — Router + Specialist Agents
Build specialist agents with focused system prompts, then route
user queries to the right specialist using LLM-based classification.

Run:  python start.py
"""
from __future__ import annotations
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEPARTMENTS = ["medical", "tactical", "comms"]

SPECIALIST_PROMPTS = {
    "medical": (
        "You are the Medical Officer aboard the DSS Pathfinder. "
        "You handle all questions about crew health, injuries, quarantine "
        "protocols, radiation exposure, and bio-hazard containment. "
        "Answer concisely with clinical precision."
    ),
    "tactical": (
        "You are the Tactical Officer aboard the DSS Pathfinder. "
        "You handle all questions about threat assessment, shields, "
        "weapons systems, evasive maneuvers, and defense protocols. "
        "Answer concisely and with authority."
    ),
    "comms": (
        "You are the Communications Officer aboard the DSS Pathfinder. "
        "You handle all questions about hailing frequencies, signal "
        "decryption, subspace relays, distress beacons, and encrypted "
        "transmissions. Answer concisely and cite signal data where possible."
    ),
}


def classify_query(query: str, client: OpenAI) -> str:
    """Use the LLM to classify a query into a department.

    Returns one of: 'medical', 'tactical', 'comms'.

    Steps:
        1. Call client.chat.completions.create with gpt-4o-mini
        2. Use response_format={"type": "json_object"}
        3. System prompt: instruct the model to classify into one of the
           three departments and return JSON: {"department": "<name>"}
        4. Parse the JSON response and return the department string
        5. If parsing fails or department is invalid, default to "medical"
    """
    # TODO: implement LLM-based classification
    raise NotImplementedError("TODO")


def specialist_agent(department: str, query: str, client: OpenAI) -> str:
    """Run a specialist agent for the given department.

    Steps:
        1. Look up the system prompt from SPECIALIST_PROMPTS for the department
           (fall back to "medical" for unknown departments)
        2. Call client.chat.completions.create with gpt-4o-mini
        3. Pass the system prompt and the user's query
        4. Return the response text
    """
    # TODO: implement specialist agent
    raise NotImplementedError("TODO")


def route_and_respond(query: str, client: OpenAI) -> dict:
    """Classify a query, dispatch to the right specialist, return the result.

    Steps:
        1. Call classify_query to determine the department
        2. Call specialist_agent with the department and query
        3. Return {"department": department, "response": response}
    """
    # TODO: implement routing pipeline
    raise NotImplementedError("TODO")


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
