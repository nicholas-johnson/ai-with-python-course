"""Supervisor-Critic pipeline — provided from Exercise 02 solution."""
from __future__ import annotations
import json
from openai import OpenAI
from agents import classify_query, specialist_agent, DEPARTMENTS, SPECIALIST_PROMPTS


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
    def __init__(self, client: OpenAI):
        self.client = client

    def review(self, query: str, response: str) -> dict:
        """Return {"approved": bool, "feedback": str}."""
        result = self.client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": CRITIC_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Original query: {query}\n\n"
                        f"Specialist response: {response}\n\n"
                        "Evaluate this response."
                    ),
                },
            ],
        )
        try:
            data = json.loads(result.choices[0].message.content)
            return {
                "approved": bool(data.get("approved", False)),
                "feedback": str(data.get("feedback", "")),
            }
        except (json.JSONDecodeError, AttributeError):
            return {"approved": True, "feedback": "Unable to parse review."}


class SupervisorAgent:
    def __init__(self, client: OpenAI, max_revisions: int = 2):
        self.client = client
        self.max_revisions = max_revisions
        self.critic = CriticAgent(client)

    def run(self, query: str) -> dict:
        """Return {"department": str, "response": str, "trace": list}."""
        trace = []

        department = classify_query(query, self.client)
        trace.append({"agent": "router", "department": department})

        response = specialist_agent(department, query, self.client)
        trace.append({"agent": "specialist", "department": department, "response": response})

        for _ in range(self.max_revisions + 1):
            review = self.critic.review(query, response)
            trace.append({"agent": "critic", "approved": review["approved"], "feedback": review["feedback"]})

            if review["approved"]:
                break

            response = self._revise(department, query, response, review["feedback"])
            trace.append({"agent": "specialist", "department": department, "response": response, "revision": True})

        return {"department": department, "response": response, "trace": trace}

    def _revise(self, department: str, query: str, previous: str, feedback: str) -> str:
        system_prompt = SPECIALIST_PROMPTS.get(department, SPECIALIST_PROMPTS["science"])
        result = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
                {"role": "assistant", "content": previous},
                {
                    "role": "user",
                    "content": f"The quality reviewer rejected your response:\n{feedback}\n\nPlease revise.",
                },
            ],
        )
        return result.choices[0].message.content


def run_supervised_query(query: str, client: OpenAI, max_revisions: int = 2) -> dict:
    supervisor = SupervisorAgent(client, max_revisions=max_revisions)
    return supervisor.run(query)
