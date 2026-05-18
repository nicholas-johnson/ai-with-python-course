"""
Module 4 Demo — Multimodal: Vision + Audio
Run:  python module-04-genai-strategies/demo/demo.py

Shows GPT-4o analysing an image and Whisper transcribing audio.
Uses sample files bundled in this directory.

Requires: OPENAI_API_KEY environment variable.
"""

import base64
import io
import json
from pathlib import Path

from openai import OpenAI

DEMO_DIR = Path(__file__).parent


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_vision(client: OpenAI):
    section("Part 1: Vision — GPT-4o Image Analysis")

    image_path = DEMO_DIR / "sample.png"
    img_b64 = base64.b64encode(image_path.read_bytes()).decode()

    print(f"  Image: {image_path.name} ({image_path.stat().st_size} bytes)")
    print("  Sending to GPT-4o for analysis...\n")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an image analysis assistant. Respond with a JSON object "
                    'containing "description" (string) and "key_points" (list of strings). '
                    "Only output valid JSON, no markdown."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe and analyse this image in detail."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                    },
                ],
            },
        ],
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content or "{}")
    print(f"  Description: {result.get('description', '(none)')}\n")
    print("  Key points:")
    for point in result.get("key_points", []):
        print(f"    • {point}")

    print(f"\n  Tokens: {response.usage.prompt_tokens} prompt + {response.usage.completion_tokens} completion")
    print("\n  The same API call powers the /vision endpoint in Exercise 2.")


def demo_whisper(client: OpenAI):
    section("Part 2: Audio — Whisper Transcription")

    audio_path = DEMO_DIR / "sample.wav"
    audio_bytes = audio_path.read_bytes()

    print(f"  Audio: {audio_path.name} ({len(audio_bytes)} bytes)")
    print("  Sending to Whisper for transcription...\n")

    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "sample.wav"

    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
    )

    text = transcript.text.strip()
    if text:
        print(f"  Transcript: \"{text}\"")
    else:
        print("  Transcript: (empty — the sample is a tone, not speech)")
        print("  Try replacing sample.wav with a real voice recording!")

    print("\n  The same API call powers the /transcribe endpoint in Exercise 2.")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    client = OpenAI()

    demo_vision(client)
    input("\n  [press Enter to continue]\n")
    demo_whisper(client)

    print("\n" + "=" * 60)
    print("  Demo complete. Ready for exercises!")
    print("=" * 60)
