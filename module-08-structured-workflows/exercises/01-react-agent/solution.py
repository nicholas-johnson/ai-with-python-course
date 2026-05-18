"""
Exercise 01 — ReAct Agent (Solution)
======================================
A ReAct loop: Thought → Action → Observation with explicit traces.

Run:  python solution.py
"""
from __future__ import annotations
import json
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

try:
    import httpx
except ImportError:
    httpx = None

# --- Tools ---
_notes: list[str] = []


def search_web(query: str) -> str:
    """Search the web for information. Returns a text summary."""
    if httpx is not None:
        try:
            resp = httpx.get(
                "https://lite.duckduckgo.com/lite",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
                follow_redirects=True,
            )
            resp.raise_for_status()
            text = re.sub(r"<[^>]+>", " ", resp.text)
            text = re.sub(r"\s+", " ", text).strip()
            snippet = text[:1500]
            if snippet:
                return f"Search results for '{query}':\n{snippet}"
        except Exception:
            pass

    return (
        f"Search results for '{query}': "
        f"[mock] Here are some relevant facts about {query}. "
        f"This is a simulated search result for demonstration purposes."
    )


def calculator(expression: str) -> str:
    """Evaluate a mathematical expression. Returns the result as a string."""
    cleaned = expression.strip()
    if not re.match(r'^[\d\s\+\-\*/\.\(\)\*]+$', cleaned):
        return f"Error: unsafe expression '{expression}'"
    try:
        result = eval(cleaned, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def take_note(content: str) -> str:
    """Save a note for later reference. Returns confirmation."""
    _notes.append(content)
    return f"Note saved ({len(_notes)} total)."


def read_notes() -> str:
    """Read all saved notes. Returns notes as numbered list."""
    if not _notes:
        return "No notes yet."
    return "\n".join(f"{i}. {note}" for i, note in enumerate(_notes, 1))


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
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a mathematical expression. Returns the result as a string.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The math expression to evaluate, e.g. '2 + 2' or '(10 * 5) / 3'",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "take_note",
            "description": "Save a note for later reference. Returns confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The note content to save",
                    }
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_notes",
            "description": "Read all saved notes. Returns notes as numbered list.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
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
    messages = [SYSTEM_PROMPT, {"role": "user", "content": query}]
    trace: list[dict] = []

    for _step in range(max_steps):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOL_SCHEMAS,
        )
        choice = response.choices[0].message

        if choice.tool_calls:
            messages.append(choice)
            for tool_call in choice.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                func = TOOLS.get(name)
                if func:
                    result = func(**args)
                else:
                    result = f"Unknown tool: {name}"

                trace.append({
                    "type": "tool",
                    "name": name,
                    "args": args,
                    "result": result,
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
        else:
            content = choice.content or ""
            trace.append({"type": "answer", "content": content})
            return {"answer": content, "trace": trace}

    return {
        "answer": "[Max steps reached — no final answer produced]",
        "trace": trace,
    }


def print_trace(trace: list[dict]) -> None:
    """Pretty-print a ReAct trace."""
    for i, step in enumerate(trace, 1):
        if step["type"] == "tool":
            args_str = json.dumps(step["args"], ensure_ascii=False)
            result_preview = step["result"][:200]
            print(f"  [Step {i}] \U0001f527 Tool: {step['name']}({args_str})")
            print(f"           \u2192 {result_preview}")
        elif step["type"] == "answer":
            print(f"  [Step {i}] \u2705 Answer: {step['content']}")


def main():
    client = OpenAI()
    max_steps = 5
    last_trace: list[dict] = []

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
