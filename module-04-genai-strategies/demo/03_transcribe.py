"""Part 3: Speech to text — sample.wav or the microphone."""

import io
import wave
from pathlib import Path

from openai import OpenAI

TRANSCRIBE_MODEL = "gpt-transcribe"
DEMO_DIR = Path(__file__).parent


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
    audio_data = np.asarray(sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
    ))
    sd.wait()
    print("  Recording complete.\n")

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())
    return buf.getvalue()


def demo_transcribe(client: OpenAI):
    print("=" * 60)
    print("PART 3: SPEECH TO TEXT")
    print("=" * 60)
    print()

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
    print(f"  Sending to {TRANSCRIBE_MODEL} for transcription...\n")

    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    transcript = client.audio.transcriptions.create(model=TRANSCRIBE_MODEL, file=audio_file)

    text = transcript.text.strip()
    if text:
        print(f'  Transcript: "{text}"')
    else:
        print("  Transcript: (empty — no speech detected)")
        print("  Try speaking closer to the microphone, or use a longer duration.")

    print("\n  The same API call powers the /transcribe endpoint in Exercise 2.")
