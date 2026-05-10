"""
Exercise 04 — Deploy Container
Health-check app, environment config, and Dockerfile validation.
"""

from __future__ import annotations

from typing import Any


def create_app():
    """Return a FastAPI app with a GET /health endpoint.

    The /health endpoint should return {"status": "ok"}.
    """
    raise NotImplementedError("TODO")


def load_config() -> dict[str, Any]:
    """Load configuration from environment variables.

    Return a dict with keys:
      - openai_api_key: str  (from OPENAI_API_KEY, required — raise ValueError if missing)
      - model: str           (from OPENAI_MODEL, default "gpt-4o-mini")
      - port: int            (from PORT, default 8000)
      - debug: bool          (from DEBUG, default False — "true"/"1" → True)
    """
    raise NotImplementedError("TODO")


def validate_dockerfile(dockerfile_text: str) -> list[str]:
    """Check that a Dockerfile string contains required instructions.

    Return a list of missing instruction names from:
      FROM, EXPOSE, HEALTHCHECK, CMD

    Return an empty list if all are present.
    """
    raise NotImplementedError("TODO")
