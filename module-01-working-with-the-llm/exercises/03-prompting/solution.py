"""
Exercise 03 — Prompt Engineering (solution)
"""

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Base prompts
# ---------------------------------------------------------------------------

BASE_PROMPTS = {
    "concise": (
        "You are a helpful assistant. Answer every question in one sentence maximum. "
        "Never use more than one sentence."
    ),
    "ship_ai": (
        "You are the DSS Pathfinder ship AI. You speak in a formal, precise tone. "
        "You refer to the user as 'Commander'. You provide brief situational reports "
        "when asked about ship status. You never break character."
    ),
    "step_by_step": (
        "You are a helpful assistant. Think step by step. "
        "Number each step starting from 1. Keep each step to one sentence."
    ),
    "translator": (
        "You are a French translator. Translate the user's message into French. "
        "Respond with only the French translation, nothing else."
    ),
    "classifier": (
        "You are a sentiment classifier. Classify the user's message as exactly one of: "
        "POSITIVE, NEGATIVE, or NEUTRAL. Respond with only the label, nothing else."
    ),
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def run_prompt(client, system_prompt: str, user_message: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Challenge solutions
# ---------------------------------------------------------------------------

def pirate_prompt() -> str:
    return (
        "You are a pirate. Respond to everything in exaggerated pirate speak. "
        "Use words like 'arr', 'matey', 'ye', 'ahoy', 'treasure', and 'seas'. "
        "Refer to yourself as a salty sea dog. Never break character."
    )


def bullet_prompt() -> str:
    return (
        "You are a helpful assistant. Always respond using bullet points. "
        "Each bullet point must start with '- '. "
        "Do not include any introductory sentence, closing sentence, or "
        "any text outside of the bullet points. Only output bullet points."
    )


def json_prompt() -> str:
    return (
        "You are a helpful assistant that responds only in valid JSON. "
        "Always respond with a JSON object containing an \"answer\" key "
        "with your response as the value. Example: {\"answer\": \"Paris\"}. "
        "Do not include markdown code fences, explanations, or any text "
        "outside the JSON object. Output raw JSON only."
    )


def haiku_prompt() -> str:
    return (
        "You are a haiku poet. Respond to every message with exactly one haiku. "
        "A haiku is exactly 3 lines following the 5-7-5 syllable pattern. "
        "Output only the 3 lines of the haiku, nothing else. "
        "No title, no explanation, no extra whitespace."
    )


def refusal_prompt() -> str:
    return (
        "You are a space and astronomy expert. You ONLY answer questions about "
        "space, astronomy, astrophysics, planets, stars, galaxies, spacecraft, "
        "and related topics. "
        "If the user asks about anything outside these topics, respond with exactly: "
        "\"I can only help with space and astronomy topics.\" "
        "Do not answer off-topic questions under any circumstances."
    )


def few_shot_prompt() -> str:
    return (
        "You are a ship incident classifier. Given a description of an event, "
        "respond with a category label followed by a colon and a one-line summary.\n"
        "\n"
        "Examples:\n"
        "User: The engine overheated during the night cycle.\n"
        "Assistant: ENGINEERING: Engine temperature exceeded safe operating limits.\n"
        "\n"
        "User: Crew member reported seeing lights outside the viewport.\n"
        "Assistant: OBSERVATION: Unidentified visual phenomenon reported by crew.\n"
        "\n"
        "User: The food supply inventory doesn't match the logs.\n"
        "Assistant: LOGISTICS: Discrepancy detected between inventory count and records.\n"
        "\n"
        "Follow this exact format: CATEGORY: one-line explanation. "
        "Use uppercase for the category. Do not include anything else."
    )


# ---------------------------------------------------------------------------
# Challenge registry
# ---------------------------------------------------------------------------

CHALLENGES = {
    "pirate": (pirate_prompt, "Tell me about the weather today."),
    "bullets": (bullet_prompt, "What are the benefits of exercise?"),
    "json": (json_prompt, "What is the capital of France?"),
    "haiku": (haiku_prompt, "Write about the ocean."),
    "refusal": (refusal_prompt, "How do I bake a cake?"),
    "few_shot": (few_shot_prompt, "The oxygen recycler is making a strange noise."),
}


# ---------------------------------------------------------------------------
# Interactive runner
# ---------------------------------------------------------------------------

def main() -> None:
    client = OpenAI()

    print("=== Prompt Engineering Challenges ===\n")
    print("Base prompts you can try:")
    for name in BASE_PROMPTS:
        print(f"  base:{name}")
    print("\nChallenges to complete:")
    for name in CHALLENGES:
        print(f"  {name}")
    print("\nType a name to select it, then enter messages. Type 'quit' to exit.\n")

    current_prompt = None
    current_name = None

    while True:
        if current_prompt is None:
            choice = input("Select prompt> ").strip()
            if choice.lower() in ("quit", "exit"):
                break

            if choice.startswith("base:"):
                key = choice[5:]
                if key in BASE_PROMPTS:
                    current_prompt = BASE_PROMPTS[key]
                    current_name = choice
                    print(f"\nUsing base prompt: {key}")
                    print(f"Prompt: {current_prompt[:80]}...\n")
                else:
                    print(f"Unknown base prompt: {key}\n")
                continue

            if choice in CHALLENGES:
                prompt_fn, example_msg = CHALLENGES[choice]
                prompt = prompt_fn()
                if prompt is None:
                    print(f"  '{choice}' not implemented yet — write it in start.py!\n")
                    continue
                current_prompt = prompt
                current_name = choice
                print(f"\nUsing challenge prompt: {choice}")
                print(f"Prompt: {current_prompt[:80]}...")
                print(f"Try this test message: {example_msg}\n")
            else:
                print(f"Unknown selection: {choice}\n")
            continue

        user_input = input(f"[{current_name}] You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            break
        if user_input.lower() == "back":
            current_prompt = None
            current_name = None
            print()
            continue

        response = run_prompt(client, current_prompt, user_input)
        print(f"\nAI: {response}\n")


if __name__ == "__main__":
    main()
