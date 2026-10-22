"""
Exercise 04 — Agentic RAG (Solution)

The agent decides whether to retrieve, what to search for,
and when it has enough information to answer.
"""

import json
import os
from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


SEARCH_TOOL = {
    "type": "function",
    "name": "search_documents",
    "description": (
        "Search the document database for information relevant "
        "to answering the user's question."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant documents.",
            },
        },
        "required": ["query"],
    },
}


def handle_tool_call(tool_call, search_fn) -> str:
    """
    Execute a tool call and return the result as a JSON string.
    """
    args = json.loads(tool_call.arguments)
    if tool_call.name == "search_documents":
        results = search_fn(args["query"])
        return json.dumps(results)
    return json.dumps({"error": f"Unknown tool: {tool_call.name}"})


def agentic_rag(
    client: OpenAI,
    question: str,
    search_fn,
    max_turns: int = 5,
) -> str:
    """
    Run an agentic RAG loop.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. Use the search_documents tool "
                "to find information when you need it. You can search multiple "
                "times if needed. When you have enough information, provide "
                "a clear answer."
            ),
        },
        {"role": "user", "content": question},
    ]

    for _ in range(max_turns):
        response = client.responses.create(
            model=MODEL,
            reasoning={"effort": "none"},
            input=messages,
            tools=[SEARCH_TOOL],
        )
        calls = [item for item in response.output if item.type == "function_call"]

        if not calls:
            return response.output_text

        messages += response.output
        for tool_call in calls:
            result = handle_tool_call(tool_call, search_fn)
            messages.append({
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": result,
            })

    final = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=messages,
    )
    return final.output_text
