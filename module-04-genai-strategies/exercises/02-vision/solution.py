"""
Exercise 02 — Vision (solution)
"""

from __future__ import annotations

import base64
import json
import mimetypes
import sys
from pathlib import Path
from typing import Literal

import openai
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Carried forward from Exercise 01
# ---------------------------------------------------------------------------

class MissionReport(BaseModel):
    mission_id: str
    status: Literal["active", "completed", "aborted"]
    risk_level: Literal["low", "medium", "high", "critical"]
    summary: str


SYSTEM_PROMPT = """\
You are a mission analyst for the DSS Pathfinder.
Given a free-text event description or an image, return ONLY a JSON object matching this schema:
{
  "mission_id": "string — invent a short ID if none is given",
  "status": "active | completed | aborted",
  "risk_level": "low | medium | high | critical",
  "summary": "one-sentence summary of what you observe"
}
Do not include any text outside the JSON object.\
"""


def analyse(client: openai.OpenAI, text: str) -> MissionReport:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    raw = response.choices[0].message.content
    return MissionReport.model_validate(json.loads(raw))


# ---------------------------------------------------------------------------
# Vision helpers
# ---------------------------------------------------------------------------

def encode_image(path: str | Path) -> str:
    data = Path(path).read_bytes()
    return base64.b64encode(data).decode()


def detect_mime(path: str | Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "image/png"


def analyse_image(
    client: openai.OpenAI,
    image_source: str,
    prompt: str = "Analyse this image and report any notable findings.",
) -> MissionReport:
    if image_source.startswith("http"):
        image_url = image_source
    else:
        mime = detect_mime(image_source)
        b64 = encode_image(image_source)
        image_url = f"data:{mime};base64,{b64}"

    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
    )
    raw = response.choices[0].message.content
    return MissionReport.model_validate(json.loads(raw))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python start.py <image_path_or_url>")
        print("       python start.py path/to/photo.png")
        print("       python start.py https://example.com/image.jpg")
        sys.exit(1)

    image_source = sys.argv[1]
    client = openai.OpenAI()

    print(f"Analysing: {image_source}")
    report = analyse_image(client, image_source)
    print(json.dumps(report.model_dump(), indent=2))


if __name__ == "__main__":
    main()
