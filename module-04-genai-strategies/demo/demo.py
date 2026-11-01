"""
Module 4 Demo — Multimodal: Vision + Audio
Run:  python module-04-genai-strategies/demo/demo.py

  Part 1: One image, one sentence
  Part 2: The same image, parsed into a schema
  Part 3: Speech to text

Token counting is a separate script: 04_tiktoken.py

Requires: OPENAI_API_KEY environment variable.
"""

from importlib import import_module

from dotenv import load_dotenv
from openai import OpenAI

demo_vision = import_module("01_vision").demo_vision
demo_vision_structured = import_module("02_vision_structured").demo_vision_structured
demo_transcribe = import_module("03_transcribe").demo_transcribe

DEMOS = {
    "1": ("Vision — one sentence", demo_vision),
    "2": ("Vision — structured", demo_vision_structured),
    "3": ("Speech to text", demo_transcribe),
}


def main():
    load_dotenv()
    client = OpenAI()

    print("\n" + "=" * 60)
    print("  MODULE 4 DEMO — MULTIMODAL")
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
    print("  1. Vision            — image in, output_text out")
    print("  2. Structured vision — the same call, parsed into a schema")
    print("  3. Speech to text    — audio in, transcript out")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
