"""Exercise 04 — Multimodal Analysis (solution)"""

from __future__ import annotations

import base64
import json
from typing import Any

VALID_SEVERITIES = {"low", "medium", "high", "critical"}


def prepare_image_message(
    image_bytes: bytes,
    prompt: str = "Describe any damage visible in this image.",
    media_type: str = "image/png",
) -> dict[str, Any]:
    b64 = base64.b64encode(image_bytes).decode()
    return {
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{media_type};base64,{b64}"},
            },
        ],
    }


def prepare_audio_payload(
    audio_bytes: bytes,
    filename: str = "recording.wav",
) -> dict[str, Any]:
    return {
        "file": audio_bytes,
        "filename": filename,
        "model": "whisper-1",
    }


def parse_damage_report(raw_model_text: str) -> dict[str, Any]:
    try:
        data = json.loads(raw_model_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc

    for key in ("location", "severity", "description"):
        if key not in data:
            raise ValueError(f"Missing required key: {key}")

    if data["severity"] not in VALID_SEVERITIES:
        raise ValueError(
            f"Invalid severity '{data['severity']}'; "
            f"expected one of {VALID_SEVERITIES}"
        )

    return data
