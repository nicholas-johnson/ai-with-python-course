"""
Exercise 03 — Multimodal API (solution)
"""

from __future__ import annotations

import base64
import io
import json
from typing import Literal

import openai
import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Carried forward from Exercises 01 + 02
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
    image: str | None = None
    image_url: str | None = None
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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=MissionReport)
def chat(req: ChatRequest):
    client = _get_client()
    return analyse_text(client, req.text)


@app.post("/vision", response_model=MissionReport)
def vision(req: VisionRequest):
    if req.image:
        url = f"data:image/png;base64,{req.image}"
    elif req.image_url:
        url = req.image_url
    else:
        raise HTTPException(status_code=400, detail="Provide 'image' (base64) or 'image_url'.")

    client = _get_client()
    return analyse_image(client, url, req.prompt)


@app.post("/transcribe", response_model=TranscriptResponse)
async def transcribe(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    client = _get_client()
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=(file.filename or "audio.wav", audio_bytes, file.content_type or "audio/wav"),
    )
    return TranscriptResponse(transcript=transcript.text)


if __name__ == "__main__":
    uvicorn.run("solution:app", host="0.0.0.0", port=8000, reload=True)
