"""
Exercise 02 — Supervisor-Critic Pipeline
A supervisor orchestrates specialist agents with a critic review loop.
The critic validates each response before it reaches the user.

Run:  python start.py
"""
from __future__ import annotations
from dotenv import load_dotenv
from openai import OpenAI

from agents import classify_query, specialist_agent, DEPARTMENTS, SPECIALIST_PROMPTS

load_dotenv()


CRITIC_PROMPT = (
    "You are a quality-assurance critic aboard the DSS Pathfinder. "
    "Review the specialist's response for accuracy, completeness, and "
    "potential hallucination. Return JSON: "
    '{"approved": true/false, "feedback": "<explanation>"}. '
    "Approve if the response is accurate and reasonably complete. "
    "Reject with specific feedback if you find errors, gaps, or "
    "unsupported claims."
)


class CriticAgent:
    """Reviews specialist responses and returns structured feedback."""

    def __init__(self, client: OpenAI):
        self.client = client

    def review(self, query: str, response: str) -> dict:
        """Evaluate a specialist's response for quality.

        Returns {"approved": bool, "feedback": str}.

        Steps:
            1. Call client.chat.completions.create with gpt-4o-mini and JSON mode
            2. System prompt: CRITIC_PROMPT
            3. User message: include both the original query and the specialist response
            4. Parse the JSON result into {"approved": bool, "feedback": str}
            5. On parse failure, default to approved=True
        """
        # TODO: implement critic review
        raise NotImplementedError("TODO")


class SupervisorAgent:
    """Orchestrates classify → specialist → critic review loop."""

    def __init__(self, client: OpenAI, max_revisions: int = 2):
        self.client = client
        self.max_revisions = max_revisions
        self.critic = CriticAgent(client)

    def run(self, query: str) -> dict:
        """Run the full supervised pipeline.

        Returns {"department": str, "response": str, "trace": list}.

        Steps:
            1. Classify the query using classify_query → add to trace
            2. Get a specialist response using specialist_agent → add to trace
            3. Loop up to (max_revisions + 1) times:
               a. Ask the critic to review the response → add to trace
               b. If approved, break
               c. Otherwise, revise using _revise → add to trace
            4. Return the department, final response, and full trace
        """
        # TODO: implement supervised pipeline
        raise NotImplementedError("TODO")

    def _revise(self, department: str, query: str, previous: str, feedback: str) -> str:
        """Ask the specialist to revise, incorporating critic feedback.

        Steps:
            1. Look up the system prompt for the department
            2. Build a message list: system prompt, original query,
               previous response, then a user message with the feedback
            3. Return the revised response text
        """
        # TODO: implement revision
        raise NotImplementedError("TODO")


def run_supervised_query(query: str, client: OpenAI, max_revisions: int = 2) -> dict:
    """Convenience function: create a SupervisorAgent and run a query.

    Steps:
        1. Create a SupervisorAgent with the given client and max_revisions
        2. Call supervisor.run(query)
        3. Return the result
    """
    # TODO: implement
    raise NotImplementedError("TODO")


def main():
    client = OpenAI()
    max_rev = 2
    last_trace = None

    print("=" * 60)
    print("  MODULE 9 — Supervisor-Critic Pipeline")
    print("  DSS Pathfinder Multi-Agent System")
    print("=" * 60)
    print("Commands: /trace, /max-revisions N, /agents, quit\n")

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

        if user_input == "/trace":
            if last_trace is None:
                print("[No trace yet — ask a question first]\n")
            else:
                print("[Agent Trace]")
                for i, step in enumerate(last_trace, 1):
                    print(f"  {i}. {step}")
                print()
            continue

        if user_input.startswith("/max-revisions"):
            parts = user_input.split()
            if len(parts) == 2 and parts[1].isdigit():
                max_rev = int(parts[1])
                print(f"[Max revisions set to {max_rev}]\n")
            else:
                print("[Usage: /max-revisions N]\n")
            continue

        if user_input == "/agents":
            print("[Agent Team]")
            print("  supervisor  — orchestrates the pipeline")
            print("  critic      — reviews responses for quality")
            for dept in DEPARTMENTS:
                print(f"  {dept:12s} — specialist agent")
            print()
            continue

        result = run_supervised_query(user_input, client, max_revisions=max_rev)
        last_trace = result["trace"]
        approved = any(
            step.get("agent") == "critic" and step.get("approved")
            for step in result["trace"]
        )
        status = "approved" if approved else "max revisions reached"
        print(f"[{result['department']}] ({status})")
        print(f"Agent: {result['response']}\n")


if __name__ == "__main__":
    main()
