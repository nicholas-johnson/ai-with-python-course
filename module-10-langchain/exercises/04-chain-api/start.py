"""
Exercise 04 — Chain API (CSS Horizon)
Expose the crew report classifier chain as a FastAPI service.

Run server:  uvicorn start:create_app --factory --reload
Test:        pytest test_start.py -v
"""

from __future__ import annotations

import os
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

# TODO: Import LangChain + Pydantic components
# from typing import Literal
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_openai import ChatOpenAI
# from pydantic import BaseModel, Field

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


# ---------------------------------------------------------------------------
# TODO: Build the classification chain (same pattern as exercise 01)
# ---------------------------------------------------------------------------

# class Classification(BaseModel): ...   (same schema as exercise 01)
# prompt = ChatPromptTemplate.from_messages([...])
# model = ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0, use_responses_api=True)
# chain = prompt | model.with_structured_output(Classification)


# ---------------------------------------------------------------------------
# TODO: Request models
# ---------------------------------------------------------------------------

# class ReportInput(BaseModel):
#     report: str
#
# class InvokeRequest(BaseModel):
#     input: ReportInput
#
# class InvokeResponse(BaseModel):
#     output: Classification


def create_app() -> FastAPI:
    """Return a FastAPI app with /health and /classify/invoke routes."""
    app = FastAPI(title="Horizon Report API")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    # TODO: POST /classify/invoke — await chain.ainvoke(...) and return InvokeResponse(output=...)
    # TODO (stretch): POST /classify/stream — stream chain.astream(...) as NDJSON

    return app
