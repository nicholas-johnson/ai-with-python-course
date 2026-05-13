"""
Module 1 Demo — Working with the LLM
Run:  python module-01-working-with-the-llm/demo/demo.py

Walks through the full module in one script:
  Part 1: Basic chat — single API call, message roles, the response object
  Part 2: Streaming — tokens arrive one by one, perceived latency drops
  Part 3: Prompt engineering — same question, wildly different outputs

Requires: OPENAI_API_KEY environment variable.
"""

import sys

from openai import OpenAI

MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = "You are the DSS Pathfinder ship AI. Be helpful, concise, and professional."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def chat(client: OpenAI, messages: list[dict]) -> str:
    """Non-streaming single-shot call. Returns the response text."""
    response = client.chat.completions.create(model=MODEL, messages=messages)
    return response.choices[0].message.content


def stream_response(client: OpenAI, messages: list[dict]) -> str:
    """Stream the response token by token, printing as they arrive."""
    response = client.chat.completions.create(
        model=MODEL, messages=messages, stream=True,
    )
    tokens = []
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            sys.stdout.write(content)
            sys.stdout.flush()
            tokens.append(content)
    print()
    return "".join(tokens)


def run_prompt(client: OpenAI, system_prompt: str, user_message: str) -> str:
    """One-shot call with a custom system prompt."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Part 1: Basic chat
# ---------------------------------------------------------------------------

def demo_basic_chat(client: OpenAI):
    print("=" * 60)
    print("PART 1: BASIC CHAT")
    print("=" * 60)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("\nThe message list starts with one system message.")
    print(f"  messages = {messages}\n")

    user_msg = "How many crew members are on board?"
    messages.append({"role": "user", "content": user_msg})
    print(f"User: {user_msg}")

    response = chat(client, messages)
    messages.append({"role": "assistant", "content": response})
    print(f"AI:   {response}\n")

    user_msg = "What did I just ask you?"
    messages.append({"role": "user", "content": user_msg})
    print(f"User: {user_msg}")

    response = chat(client, messages)
    messages.append({"role": "assistant", "content": response})
    print(f"AI:   {response}\n")

    print(f"Messages list now has {len(messages)} entries.")
    print("The model sees the full list every call — that's how it 'remembers'.\n")


# ---------------------------------------------------------------------------
# Part 2: Streaming
# ---------------------------------------------------------------------------

def demo_streaming(client: OpenAI):
    print("=" * 60)
    print("PART 2: STREAMING")
    print("=" * 60)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Explain how warp drives work in 2 short paragraphs."},
    ]

    print("\nWith stream=True, tokens arrive one by one.")
    print("Watch them appear:\n")

    sys.stdout.write("AI> ")
    sys.stdout.flush()
    stream_response(client, messages)
    print()


# ---------------------------------------------------------------------------
# Part 3: Prompt engineering
# ---------------------------------------------------------------------------

PROMPTS = {
    "default": "You are a helpful assistant.",
    "persona": (
        "You are a grizzled pirate captain. Respond in exaggerated pirate speak. "
        "Use words like 'arr', 'matey', 'ye', and 'ahoy'. Never break character."
    ),
    "bullets": (
        "You are a helpful assistant. Always respond using bullet points. "
        "Each bullet must start with '- '. No introductory or closing text — just bullets."
    ),
    "json": (
        "You are a helpful assistant that responds only in valid JSON. "
        'Always respond with a JSON object containing an "answer" key. '
        "No markdown fences, no explanation — raw JSON only."
    ),
    "guardrail": (
        "You are a space and astronomy expert. You ONLY answer questions about "
        "space, astronomy, planets, stars, and spacecraft. "
        "If the user asks about anything else, respond with exactly: "
        '"I can only help with space and astronomy topics."'
    ),
    "few_shot": (
        "You are a ship incident classifier. Given a description, respond with "
        "a category label and a one-line summary.\n"
        "\n"
        "Examples:\n"
        "User: The engine overheated during the night cycle.\n"
        "Assistant: ENGINEERING: Engine temperature exceeded safe operating limits.\n"
        "\n"
        "User: Crew member reported seeing lights outside the viewport.\n"
        "Assistant: OBSERVATION: Unidentified visual phenomenon reported by crew.\n"
        "\n"
        "Follow this exact format: CATEGORY: one-line explanation."
    ),
}


def demo_prompting(client: OpenAI):
    print("=" * 60)
    print("PART 3: PROMPT ENGINEERING")
    print("=" * 60)

    # Same question, different system prompts
    question = "What causes thunder?"
    print(f"\n--- Same question, different prompts ---")
    print(f'Question: "{question}"\n')

    for name in ("default", "persona", "bullets", "json"):
        prompt = PROMPTS[name]
        print(f"[{name}]")
        print(f"  System: {prompt[:70]}...")
        result = run_prompt(client, prompt, question)
        for line in result.splitlines():
            print(f"  > {line}")
        print()

    # Guardrails
    print("--- Guardrails: on-topic vs off-topic ---\n")
    guardrail = PROMPTS["guardrail"]
    print(f"  System: {guardrail[:70]}...\n")

    on_topic = "How far is Mars from Earth?"
    print(f"  On-topic:  \"{on_topic}\"")
    result = run_prompt(client, guardrail, on_topic)
    print(f"  > {result}\n")

    off_topic = "What's a good recipe for pasta?"
    print(f"  Off-topic: \"{off_topic}\"")
    result = run_prompt(client, guardrail, off_topic)
    print(f"  > {result}\n")

    # Few-shot
    print("--- Few-shot: teaching a pattern with examples ---\n")
    print("  System prompt includes 2 examples of CATEGORY: explanation format.\n")

    test_inputs = [
        "The oxygen recycler is making a strange noise.",
        "Navigation sensors lost signal for 3 seconds.",
        "A crew member filed a complaint about food quality.",
    ]
    for msg in test_inputs:
        result = run_prompt(client, PROMPTS["few_shot"], msg)
        print(f"  Input:  {msg}")
        print(f"  Output: {result}")
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    client = OpenAI()

    print("\n" + "=" * 60)
    print("  MODULE 1 DEMO — WORKING WITH THE LLM")
    print("=" * 60 + "\n")

    demo_basic_chat(client)
    demo_streaming(client)
    demo_prompting(client)

    print("=" * 60)
    print("RECAP")
    print("=" * 60)
    print()
    print("  1. chat()            — single API call, full response at once")
    print("  2. stream_response() — tokens arrive live, same total time")
    print("  3. system prompts    — persona, format, guardrails, few-shot")
    print()
    print("The system prompt controls everything.")
    print("Be specific. Be explicit. Show examples.")
    print("=" * 60)


if __name__ == "__main__":
    main()
