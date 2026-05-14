"""
Exercise 04 — Agentic RAG (Solution)

The agent decides whether to retrieve, what to search for,
and when it has enough information to answer.
"""

import json
from openai import OpenAI


SEARCH_TOOL = {
    "type": "function",
    "function": {
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
    },
}


def handle_tool_call(tool_call, search_fn) -> str:
    """
    Execute a tool call and return the result as a JSON string.
    """
    args = json.loads(tool_call.function.arguments)
    if tool_call.function.name == "search_documents":
        results = search_fn(args["query"])
        return json.dumps(results)
    return json.dumps({"error": f"Unknown tool: {tool_call.function.name}"})


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
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=[SEARCH_TOOL],
        )
        message = response.choices[0].message

        if not message.tool_calls:
            return message.content

        messages.append(message)
        for tool_call in message.tool_calls:
            result = handle_tool_call(tool_call, search_fn)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    final = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    return final.choices[0].message.content
