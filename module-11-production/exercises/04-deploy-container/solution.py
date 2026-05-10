"""Exercise 04 — Deploy Container (solution)"""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI

REQUIRED_INSTRUCTIONS = ["FROM", "EXPOSE", "HEALTHCHECK", "CMD"]


def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


def load_config() -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    debug_raw = os.environ.get("DEBUG", "false").lower()

    return {
        "openai_api_key": api_key,
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "port": int(os.environ.get("PORT", "8000")),
        "debug": debug_raw in ("true", "1", "yes"),
    }


def validate_dockerfile(dockerfile_text: str) -> list[str]:
    upper = dockerfile_text.upper()
    missing = []
    for instr in REQUIRED_INSTRUCTIONS:
        if instr not in upper:
            missing.append(instr)
    return missing
