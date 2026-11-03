"""
Exercise 01 — ReAct Agent
Build a ReAct loop: Thought → Action → Observation with explicit traces.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

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

# Tools that change state. After one of these runs, an earlier read may now
# return something different, so the repeat guard has to forget what it saw.
MUTATING_TOOLS = {"take_note"}

TOOL_SCHEMAS = [
    # TODO: define OpenAI function schemas for each tool
    # Each entry should look like:
    # {
    #     "type": "function",
    #     "name": "search_web",
    #     "description": "Search the web for information.",
    #     "parameters": {
    #         "type": "object",
    #         "properties": {
    #             "query": {"type": "string", "description": "The search query"}
    #         },
    #         "required": ["query"],
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
    """Run a ReAct loop with three guards: step budget, repeat detection, forced finish."""
    # TODO: implement the ReAct loop
    # 1. Start with messages = [SYSTEM_PROMPT, {"role": "user", "content": query}]
    #    Also keep `seen = set()` to remember which tool calls you have made.
    # 2. Loop up to max_steps times                           <-- GUARD 1: step budget
    # 3. Call client.responses.create(model=MODEL, reasoning={"effort": "none"},
    #                                 input=messages, tools=TOOL_SCHEMAS)
    # 4. calls = [item for item in response.output if item.type == "function_call"]
    #    If there are calls:
    #    a. Add the model's output to the history: messages += response.output
    #    b. For each call, build signature = (name, json.dumps(args, sort_keys=True))
    #       - If signature is in `seen`:                      <-- GUARD 2: no progress
    #           do NOT run the tool. Use a nudge string as the result, e.g.
    #           "You already called {name} with these arguments..."
    #           and add {"type": "guard", "name": name, "args": args} to the trace.
    #       - Otherwise: add it to `seen`, look up TOOLS[name], call it, and add
    #           {"type": "tool", "name": name, "args": args, "result": result} to the trace.
    #           If name is in MUTATING_TOOLS, reset `seen` to just this signature —
    #           the state changed, so an earlier read is worth doing again.
    #    c. Either way, append
    #       {"type": "function_call_output", "call_id": ..., "output": result} to messages
    #    d. Loop back to step 3
    # 5. Otherwise (no calls), content = response.output_text:
    #    a. Add {"type": "answer", "content": content} to trace
    #    b. Return {"answer": content, "trace": trace, "stop_reason": "answered"}
    # 6. If the loop runs out of steps:                       <-- GUARD 3: forced finish
    #    a. Append a user message telling the model it is out of steps and must
    #       answer now with whatever it has.
    #    b. Make one final call WITHOUT tools, trace the answer, and return it with
    #       stop_reason="budget_exhausted". Never return None.
    raise NotImplementedError("TODO")


def print_trace(trace: list[dict]) -> None:
    """Pretty-print a ReAct trace."""
    # TODO: for each step in trace, print formatted output:
    #   Tool steps:   [Step N] 🔧 Tool: name(args) → result
    #   Guard steps:  [Step N] ⛔ Repeat blocked: name(args)
    #   Answer step:  [Step N] ✅ Answer: content
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
        print(f"\nAnswer: {result['answer']}")
        print(f"[stopped: {result['stop_reason']}]\n")


if __name__ == "__main__":
    main()
