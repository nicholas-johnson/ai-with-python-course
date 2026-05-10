"""
Exercise 04 — Multimodal Analysis
Prepare vision and audio payloads for the LLM and parse structured results.
"""

from __future__ import annotations

import base64
from typing import Any


def prepare_image_message(
    image_bytes: bytes,
    prompt: str = "Describe any damage visible in this image.",
    media_type: str = "image/png",
) -> dict[str, Any]:
    """Return an OpenAI-compatible user message with an image content part.

    The message should contain two content parts:
      1. A text part with the prompt.
      2. An image_url part with a base64 data URI built from *image_bytes*.
    """
    raise NotImplementedError("TODO")


def prepare_audio_payload(
    audio_bytes: bytes,
    filename: str = "recording.wav",
) -> dict[str, Any]:
    """Return a dict with keys 'file' (the raw bytes) and 'filename'
    suitable for posting to a transcription endpoint.  Optionally include
    a 'model' key defaulting to 'whisper-1'.
    """
    raise NotImplementedError("TODO")


def parse_damage_report(raw_model_text: str) -> dict[str, Any]:
    """Parse the model's vision response into a structured damage report.

    Expected JSON keys: location (str), severity (low|medium|high|critical),
    description (str).  Raise ValueError on invalid JSON.
    """
    raise NotImplementedError("TODO")
