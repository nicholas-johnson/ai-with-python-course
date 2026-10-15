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
# import json
# from fastapi.responses import StreamingResponse
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import JsonOutputParser
# from langchain_openai import ChatOpenAI
# from pydantic import BaseModel

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


# ---------------------------------------------------------------------------
# TODO: Build the classification chain (same pattern as exercise 01)
# ---------------------------------------------------------------------------

# prompt = ChatPromptTemplate.from_messages([...])
# chain = prompt | ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0) | JsonOutputParser()


# ---------------------------------------------------------------------------
# TODO: Request models
# ---------------------------------------------------------------------------

# class ReportInput(BaseModel):
#     report: str
#
# class InvokeRequest(BaseModel):
#     input: ReportInput


def create_app() -> FastAPI:
    """Return a FastAPI app with /health and /classify/invoke routes."""
    app = FastAPI(title="Horizon Report API")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    # TODO: POST /classify/invoke — await chain.ainvoke(...) and return {"output": ...}
    # TODO (stretch): POST /classify/stream — stream chain.astream(...) as NDJSON

    return app
