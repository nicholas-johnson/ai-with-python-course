"""
Exercise 02 — Vision
Send images to GPT-4o and get structured analysis back.

Run:  python start.py <image_path_or_url>
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
# Carried forward from Exercise 01 (solution)
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
# 1. encode_image() — read a local file and return base64
# ---------------------------------------------------------------------------

def encode_image(path: str | Path) -> str:
    """Read an image file and return it as a base64-encoded string.

    Also return the MIME type (e.g. "image/png") so the caller can
    build a proper data URI.
    """
    # TODO: implement — read the file bytes, base64-encode, return the string
    raise NotImplementedError("TODO")


def detect_mime(path: str | Path) -> str:
    """Return the MIME type for an image file, defaulting to image/png."""
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "image/png"


# ---------------------------------------------------------------------------
# 2. analyse_image() — multimodal call returning a MissionReport
# ---------------------------------------------------------------------------

def analyse_image(
    client: openai.OpenAI,
    image_source: str,
    prompt: str = "Analyse this image and report any notable findings.",
) -> MissionReport:
    """Send an image to GPT-4o and return a validated MissionReport.

    *image_source* is either:
      - A local file path (encode it with encode_image + detect_mime)
      - A URL starting with "http" (use it directly as an image_url)

    Build a user message with two content parts:
      1. {"type": "text", "text": prompt}
      2. {"type": "image_url", "image_url": {"url": ...}}

    Use response_format={"type": "json_object"} and the SYSTEM_PROMPT.
    Parse the response into a MissionReport.
    """
    # TODO: implement
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# 3. CLI
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
