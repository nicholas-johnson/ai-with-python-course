"""
Module 8 — Demo 01: ReAct Loop

Interactive walkthrough of the ReAct pattern (Reason → Act → Observe).
Uses real OpenAI calls with simple tools to show the agent's reasoning trace.

Run:  python module-08-structured-workflows/demo/01_react.py
"""
from __future__ import annotations

import json
import re
import httpx
from openai import OpenAI


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

_notes: list[str] = []


def search_web(query: str) -> str:
    """Search the web for information."""
    try:
        resp = httpx.get(
            "https://lite.duckduckgo.com/lite",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        text = re.sub(r"<[^>]+>", " ", resp.text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:2000] if text else "No results found."
    except Exception as e:
        return f"Search error: {e}"


def calculator(expression: str) -> str:
    """Evaluate a mathematical expression safely."""
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return "Error: only digits and basic operators allowed"
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def take_note(content: str) -> str:
    """Save a note for later reference."""
    _notes.append(content)
    return f"Note saved ({len(_notes)} total)."


def read_notes() -> str:
    """Read all saved notes."""
    if not _notes:
        return "No notes yet."
    return "\n".join(f"{i+1}. {n}" for i, n in enumerate(_notes))


TOOLS = {
    "search_web": search_web,
    "calculator": calculator,
    "take_note": take_note,
    "read_notes": read_notes,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for information. Returns a text summary.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Search query"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a mathematical expression. Returns the result.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "Math expression"}},
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "take_note",
            "description": "Save a note for later reference.",
            "parameters": {
                "type": "object",
                "properties": {"content": {"type": "string", "description": "Note content"}},
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_notes",
            "description": "Read all saved notes.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a helpful research assistant. You have access to tools for web search, "
        "calculation, and note-taking. Think step by step. Use tools when needed. "
        "When you have enough information, provide a clear final answer."
    ),
}


# ---------------------------------------------------------------------------
# ReAct loop
# ---------------------------------------------------------------------------

def run_react(query: str, client: OpenAI, max_steps: int = 5) -> dict:
    messages = [SYSTEM_PROMPT, {"role": "user", "content": query}]
    trace = []

    for step in range(max_steps):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        msg = response.choices[0].message

        if msg.content:
            trace.append({"type": "thought", "content": msg.content})

        if not msg.tool_calls:
            trace.append({"type": "answer", "content": msg.content or "(no response)"})
            return {"answer": msg.content, "trace": trace}

        messages.append(msg)

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)
            trace.append({"type": "action", "tool": fn_name, "args": fn_args})

            result = TOOLS[fn_name](**fn_args)
            trace.append({"type": "observation", "tool": fn_name, "result": result[:500]})

            messages.append({
                "role": "tool",
                "content": result,
                "tool_call_id": tc.id,
            })

    return {"answer": "(max steps reached)", "trace": trace}


def print_trace(trace: list[dict]) -> None:
    for i, step in enumerate(trace):
        if step["type"] == "thought":
            print(f"  [{i+1}] Thought: {step['content'][:200]}")
        elif step["type"] == "action":
            print(f"  [{i+1}] Action:  {step['tool']}({json.dumps(step['args'])})")
        elif step["type"] == "observation":
            print(f"  [{i+1}] Observe: {step['result'][:200]}")
        elif step["type"] == "answer":
            print(f"  [{i+1}] Answer:  {step['content'][:200]}")
    print()


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def wait():
    input("\n--- Press Enter to continue ---\n")


def main():
    client = OpenAI()

    print("=" * 60)
    print("  MODULE 8 DEMO — ReAct Loop")
    print("=" * 60)

    print("\n## ReAct: Reason → Act → Observe\n")
    print("The agent thinks step by step, calls tools when needed,")
    print("observes results, and continues until it has an answer.\n")

    queries = [
        "What is the population of France divided by the area of Germany in km²?",
        "Search for the latest news about Mars exploration and save the key findings as a note.",
    ]

    for query in queries:
        print(f"Query: {query}\n")
        result = run_react(query, client, max_steps=8)
        print("Trace:")
        print_trace(result["trace"])
        print(f"Final Answer: {result['answer']}\n")
        wait()

    print("## Interactive — Try your own queries\n")
    print("Type a question, or 'quit' to end.\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input or user_input.lower() == "quit":
            break
        result = run_react(user_input, client, max_steps=8)
        print("\nTrace:")
        print_trace(result["trace"])
        print(f"Answer: {result['answer']}\n")

    print("Done.")


if __name__ == "__main__":
    main()
