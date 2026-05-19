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
import wave
from pathlib import Path

from openai import OpenAI

DEMO_DIR = Path(__file__).parent


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_vision(client: OpenAI):
    section("Part 1: Vision — GPT-4o Image Analysis")

    image_path = DEMO_DIR / "sample.webp"
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


def record_audio(duration: int = 5, sample_rate: int = 16000) -> bytes:
    """Record from the microphone and return WAV bytes."""
    try:
        import numpy as np
        import sounddevice as sd
    except ImportError:
        print("  ERROR: sounddevice/numpy not installed.")
        print("  Run:  pip install 'deep-space-ops[audio]'")
        return b""

    print(f"  Recording for {duration} seconds — speak now!")
    audio_data = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
    )
    sd.wait()
    print("  Recording complete.\n")

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())
    return buf.getvalue()


def demo_whisper(client: OpenAI):
    section("Part 2: Audio — Whisper Transcription")

    print("  [1] Use sample.wav")
    print("  [2] Record from microphone")
    choice = input("\n  Choose audio source: ").strip()

    if choice == "2":
        duration_str = input("  Duration in seconds [5]: ").strip()
        duration = int(duration_str) if duration_str.isdigit() else 5
        audio_bytes = record_audio(duration=duration)
        if not audio_bytes:
            return
        filename = "recording.wav"
    else:
        audio_path = DEMO_DIR / "sample.wav"
        audio_bytes = audio_path.read_bytes()
        filename = audio_path.name

    print(f"  Audio: {filename} ({len(audio_bytes)} bytes)")
    print("  Sending to Whisper for transcription...\n")

    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
    )

    text = transcript.text.strip()
    if text:
        print(f"  Transcript: \"{text}\"")
    else:
        print("  Transcript: (empty — no speech detected)")
        print("  Try speaking closer to the microphone, or use a longer duration.")

    print("\n  The same API call powers the /transcribe endpoint in Exercise 2.")


DEMOS = [
    ("Vision — GPT-4o Image Analysis", demo_vision),
    ("Audio — Whisper Transcription", demo_whisper),
]


def show_menu():
    print(f"\n{'='*60}")
    print("  Module 4 Demo — Multimodal: Vision + Audio")
    print(f"{'='*60}\n")
    for i, (title, _) in enumerate(DEMOS, 1):
        print(f"  [{i}] {title}")
    print(f"\n  [q] Quit")
    print()


def main():
    from dotenv import load_dotenv
    load_dotenv()

    client = OpenAI()

    while True:
        show_menu()
        choice = input("  Choose a demo: ").strip().lower()

        if choice == "q":
            break
        if choice.isdigit() and 1 <= int(choice) <= len(DEMOS):
            title, func = DEMOS[int(choice) - 1]
            func(client)
            input("\n  [press Enter to return to menu]\n")
        else:
            print("  Invalid choice, try again.")

    print(f"\n{'='*60}")
    print("  Done. Ready for exercises!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
