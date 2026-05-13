"""
Exercise 03 — Multimodal API
FastAPI app with /chat, /vision, /transcribe, and /health endpoints.

Run:  python start.py          (starts uvicorn on port 8000)
Docs: http://localhost:8000/docs
"""

from __future__ import annotations

import base64
import io
import json
from typing import Literal

import openai
import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Carried forward from Exercises 01 + 02 (solutions)
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


def _get_client() -> openai.OpenAI:
    return openai.OpenAI()


def analyse_text(client: openai.OpenAI, text: str) -> MissionReport:
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


def analyse_image(
    client: openai.OpenAI,
    image_url: str,
    prompt: str = "Analyse this image and report any notable findings.",
) -> MissionReport:
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
# Request / response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    text: str


class VisionRequest(BaseModel):
    image: str | None = None       # base64-encoded image data
    image_url: str | None = None   # or a public URL
    prompt: str = "Analyse this image and report any notable findings."


class TranscriptResponse(BaseModel):
    transcript: str


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="Pathfinder Multimodal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# TODO: Implement the four endpoints below.


@app.get("/health")
def health():
    """Return {"status": "ok"}."""
    # TODO: implement
    raise NotImplementedError("TODO")


@app.post("/chat", response_model=MissionReport)
def chat(req: ChatRequest):
    """Accept a text description, return a structured MissionReport.

    Use analyse_text() with _get_client().
    """
    # TODO: implement
    raise NotImplementedError("TODO")


@app.post("/vision", response_model=MissionReport)
def vision(req: VisionRequest):
    """Accept an image (base64 or URL), return a structured MissionReport.

    If req.image is provided, build a data URI: "data:image/png;base64,{req.image}"
    If req.image_url is provided, use it directly.
    Raise an HTTPException(400) if neither is provided.
    Use analyse_image() with _get_client().
    """
    # TODO: implement
    raise NotImplementedError("TODO")


@app.post("/transcribe", response_model=TranscriptResponse)
async def transcribe(file: UploadFile = File(...)):
    """Accept an audio file upload, transcribe with Whisper, return text.

    Use client.audio.transcriptions.create(model="whisper-1", file=...).
    The file parameter should be a tuple of (filename, file_bytes, content_type).
    """
    # TODO: implement
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# Run with: python start.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("start:app", host="0.0.0.0", port=8000, reload=True)
