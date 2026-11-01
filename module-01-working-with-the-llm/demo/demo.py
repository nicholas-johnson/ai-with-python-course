"""
Module 1 Demo — Working with the LLM
Run:  python module-01-working-with-the-llm/demo/demo.py

Walks through the full module in one script:
  Part 1: Chat Completions — one call, print the reply
  Part 2: Responses API — one call, print the reply
  Part 3: The chat loop — message list growing
  Part 4: Streaming — tokens arrive one by one
  Part 5: Prompt engineering — same question, wildly different outputs

Requires: OPENAI_API_KEY environment variable.
"""

from dotenv import load_dotenv
from openai import OpenAI

from basic_chat import demo_basic_chat
from completions import demo_completions
from prompting import demo_prompting
from responses import demo_responses
from streaming import demo_streaming, demo_streaming_clean

DEMOS = {
    "1":  ("Chat Completions",        demo_completions),
    "2":  ("Responses API",           demo_responses),
    "3":  ("The chat loop",           demo_basic_chat),
    "4":  ("Streaming (with events)", demo_streaming),
    "4b": ("Streaming (clean)",       demo_streaming_clean),
    "5":  ("Prompt engineering",      demo_prompting),
}


def main():
    load_dotenv()
    client = OpenAI()

    print("\n" + "=" * 60)
    print("  MODULE 1 DEMO — WORKING WITH THE LLM")
    print("=" * 60)

    while True:
        print("\nPick a section:\n")
        for key, (label, _) in DEMOS.items():
            print(f"  {key}. {label}")
        print(f"  q. Quit\n")

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
    print("RECAP")
    print("=" * 60)
    print()
    print("  1. Chat Completions  — messages, choices[0].message.content")
    print("  2. Responses API     — instructions, input, output_text")
    print("  3. the chat loop     — append, call, append, repeat")
    print("  4. stream_response() — tokens arrive live, same total time")
    print("  5. system prompts    — persona, format, guardrails, few-shot")
    print()
    print("The system prompt controls everything.")
    print("Be specific. Be explicit. Show examples.")
    print("=" * 60)


if __name__ == "__main__":
    main()
