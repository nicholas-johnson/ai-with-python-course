"""
Exercise 01 — ReAct Agent
Build a ReAct loop: Thought → Action → Observation with explicit traces.
"""
from __future__ import annotations
import json
from openai import OpenAI

# --- Tools ---
_notes: list[str] = []


def search_web(query: str) -> str:
    """Search the web for information. Returns a text summary."""
    # TODO: use httpx to GET https://lite.duckduckgo.com/lite?q={query}
    # Parse out text snippets from the response.
    # If the request fails, return a mock result like:
    #   f"Search results for '{query}': [mock] Here are some relevant facts..."
    raise NotImplementedError("TODO")


def calculator(expression: str) -> str:
    """Evaluate a mathematical expression. Returns the result as a string."""
    # TODO: validate that expression contains only safe characters
    # (digits, +, -, *, /, **, (, ), ., spaces)
    # Then eval() it and return str(result)
    raise NotImplementedError("TODO")


def take_note(content: str) -> str:
    """Save a note for later reference. Returns confirmation."""
    # TODO: append content to _notes, return f"Note saved ({len(_notes)} total)."
    raise NotImplementedError("TODO")


def read_notes() -> str:
    """Read all saved notes. Returns notes as numbered list."""
    # TODO: if _notes is empty return "No notes yet."
    # Otherwise return numbered list: "1. first note\n2. second note\n..."
    raise NotImplementedError("TODO")


TOOLS = {
    "search_web": search_web,
    "calculator": calculator,
    "take_note": take_note,
    "read_notes": read_notes,
}

TOOL_SCHEMAS = [
    # TODO: define OpenAI function schemas for each tool
    # Each entry should look like:
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "search_web",
    #         "description": "Search the web for information.",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "query": {"type": "string", "description": "The search query"}
    #             },
    #             "required": ["query"],
    #         },
    #     },
    # }
]

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a helpful research assistant. You have access to tools for web search, "
        "calculation, and note-taking. Think step by step. Use tools when needed to find "
        "accurate information. When you have enough information, provide a final answer."
    ),
}


def run_react(query: str, client: OpenAI, max_steps: int = 5) -> dict:
    """Run a ReAct loop: send query, handle tool calls, return trace + answer."""
    # TODO: implement the ReAct loop
    # 1. Start with messages = [SYSTEM_PROMPT, {"role": "user", "content": query}]
    # 2. Call client.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=TOOL_SCHEMAS)
    # 3. If response has tool_calls:
    #    a. Append the assistant message to messages
    #    b. For each tool_call: look up TOOLS[name], parse args, call it
    #    c. Append {"role": "tool", "tool_call_id": ..., "content": result} to messages
    #    d. Add {"type": "tool", "name": name, "args": args, "result": result} to trace
    #    e. Loop back to step 2
    # 4. If response has content (no tool_calls):
    #    a. Add {"type": "answer", "content": content} to trace
    #    b. Return {"answer": content, "trace": trace}
    # 5. Stop after max_steps iterations
    raise NotImplementedError("TODO")


def print_trace(trace: list[dict]) -> None:
    """Pretty-print a ReAct trace."""
    # TODO: for each step in trace, print formatted output:
    #   Tool steps:  [Step N] 🔧 Tool: name(args) → result
    #   Answer step: [Step N] ✅ Answer: content
    raise NotImplementedError("TODO")


def main():
    client = OpenAI()
    max_steps = 5
    last_trace = []

    print("=== ReAct Agent ===")
    print("Commands: /trace, /tools, /steps N, quit\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            break

        if user_input == "/trace":
            if last_trace:
                print_trace(last_trace)
            else:
                print("[No trace yet]\n")
            continue

        if user_input == "/tools":
            for name in TOOLS:
                print(f"  - {name}")
            print()
            continue

        if user_input.startswith("/steps "):
            try:
                max_steps = int(user_input.split()[1])
                print(f"[Max steps set to {max_steps}]\n")
            except ValueError:
                print("[Invalid number]\n")
            continue

        result = run_react(user_input, client, max_steps)
        last_trace = result["trace"]
        print_trace(last_trace)
        print(f"\nAnswer: {result['answer']}\n")


if __name__ == "__main__":
    main()
