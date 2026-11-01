"""
Module 2 Demo — Tool Calling
Run:  python module-02-tool-calling/demo/demo.py

  Part 1: One tool call — the model asks, we run the function
  Part 2: Message flow — live chat, trace every item
  Part 3: Tool registry — decorator-registered tools
  Part 4: Guarded agent — allowlist, rate limit, redaction, audit

Requires: OPENAI_API_KEY environment variable.
"""

from importlib import import_module

from dotenv import load_dotenv
from openai import OpenAI

demo_tool_call = import_module("01_tool_call").demo_tool_call
demo_message_format = import_module("02_message_flow").demo_message_format
demo_tool_registry = import_module("03_tool_registry").demo_tool_registry
demo_safety_rails = import_module("04_safety_rails").demo_safety_rails

DEMOS = {
    "1": ("One tool call", demo_tool_call),
    "2": ("Message flow", demo_message_format),
    "3": ("Tool registry", demo_tool_registry),
    "4": ("Guarded agent", demo_safety_rails),
}


def main():
    load_dotenv()
    client = OpenAI()

    print("\n" + "=" * 60)
    print("  MODULE 2 DEMO — TOOL CALLING")
    print("=" * 60)

    while True:
        print("\nPick a section:\n")
        for key, (label, _) in DEMOS.items():
            print(f"  {key}. {label}")
        print("  q. Quit\n")

        try:
            choice = input("Enter choice> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice in ("q", "quit", ""):
            break
        elif choice in DEMOS:
            _, fn = DEMOS[choice]
            print()
            fn(client)
        else:
            print(f"Unknown option: {choice}")

    print("\n" + "=" * 60)
    print("  RECAP")
    print("=" * 60)
    print()
    print("  1. One tool call   — function_call in, function result out")
    print("  2. Message flow    — system → user → function_call → output → assistant")
    print("  3. Tool registry   — @register decorator, schema + handler in one place")
    print("  4. Guarded agent   — allowlist, rate limiter, redaction, audit log")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
