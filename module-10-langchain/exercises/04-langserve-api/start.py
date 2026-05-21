"""
Exercise 04 — LangServe API (CSS Horizon)
Expose the crew report classifier as a FastAPI service.

Run server:  uvicorn start:create_app --factory --reload
Test:        pytest test_start.py -v
"""

from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

# TODO: Import LangChain + LangServe components
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import JsonOutputParser
# from langchain_openai import ChatOpenAI
# from langserve import add_routes

MODEL = "gpt-4o-mini"


# ---------------------------------------------------------------------------
# TODO: Build the classification chain (same pattern as exercise 01)
# ---------------------------------------------------------------------------

# prompt = ChatPromptTemplate.from_messages([...])
# chain = prompt | ChatOpenAI(model=MODEL, temperature=0) | JsonOutputParser()


def create_app() -> FastAPI:
    """Return a FastAPI app with /health and LangServe /classify routes."""
    app = FastAPI(title="Horizon Report API")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    # TODO: add_routes(app, chain, path="/classify")

    return app
