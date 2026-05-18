"""
Exercise 03 — Prompt Engineering
Write system prompts that make the LLM behave in specific ways.

The run_prompt() helper and the interactive main() are provided.
Study the BASE_PROMPTS examples, then complete each challenge function.
"""

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Base prompts — study these before writing your own
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
# Helper — handles the API call so you can focus on prompts
# ---------------------------------------------------------------------------

def run_prompt(client, system_prompt: str, user_message: str) -> str:
    """Call the LLM with a system prompt and user message. Return the response text."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Challenges — write a system prompt for each one
# ---------------------------------------------------------------------------

def pirate_prompt() -> str:
    """
    Return a system prompt that makes the AI talk like a pirate.

    The response should include pirate-flavoured language — words like
    "arr", "matey", "ye", "ahoy", "treasure", "seas", etc.

    Hint: tell the model WHO it is and HOW it should speak.
    """
    # TODO: return a system prompt string
    pass


def bullet_prompt() -> str:
    """
    Return a system prompt that forces the AI to answer in bullet points.

    Every answer should be a list of bullet points (lines starting with "- ").
    No introductory sentence, no closing sentence — just bullets.

    Hint: be explicit about the format and tell the model what NOT to include.
    """
    # TODO: return a system prompt string
    pass


def json_prompt() -> str:
    """
    Return a system prompt that makes the AI respond with valid JSON.

    The response should be a JSON object with at least an "answer" key.
    No markdown fences, no explanation — just raw JSON.

    Hint: specify the exact schema you want and forbid extras.
    """
    # TODO: return a system prompt string
    pass


def haiku_prompt() -> str:
    """
    Return a system prompt that makes the AI respond in haiku form.

    A haiku is exactly 3 lines (5-7-5 syllables). The response should
    contain exactly 3 non-empty lines and nothing else.

    Hint: state the format rule and tell the model to skip preamble.
    """
    # TODO: return a system prompt string
    pass


def refusal_prompt() -> str:
    """
    Return a system prompt that restricts the AI to only answering
    questions about space and astronomy.

    On-topic questions get a helpful answer. Off-topic questions
    (cooking, sports, politics, etc.) get a polite refusal like
    "I can only help with space and astronomy topics."

    Hint: define the scope clearly and give an explicit refusal template.
    """
    # TODO: return a system prompt string
    pass


def few_shot_prompt() -> str:
    """
    Return a system prompt that uses few-shot examples to teach the AI
    a specific output format: "CATEGORY: one-line explanation"

    The prompt should include 2-3 examples showing the pattern, e.g.:
      User: "The engine overheated"
      Assistant: "ENGINEERING: Engine temperature exceeded safe operating limits."

    When given a new input the model should follow the same pattern.

    Hint: put the examples directly in the system prompt.
    """
    # TODO: return a system prompt string
    pass


# ---------------------------------------------------------------------------
# Challenge registry — maps names to (prompt_fn, test_message) pairs
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
