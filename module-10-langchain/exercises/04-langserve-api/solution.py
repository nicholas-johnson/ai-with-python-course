"""
Exercise 04 — LangServe API (solution)
Run server:  uvicorn solution:create_app --factory --reload
Test:        pytest test_start.py -v
"""

from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langserve import add_routes

load_dotenv()

MODEL = "gpt-4o-mini"

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a ship incident classifier for the CSS Horizon.\n"
        "Classify the crew report into exactly one category: "
        "navigation, engineering, science, medical, or operations.\n"
        "Respond with ONLY a JSON object (no markdown fences) containing:\n"
        '  "category": one of the five categories,\n'
        '  "summary": a one-sentence summary of the report,\n'
        '  "priority": one of low, medium, high, critical.',
    ),
    ("human", "{report}"),
])

chain = prompt | ChatOpenAI(model=MODEL, temperature=0) | JsonOutputParser()


def create_app() -> FastAPI:
    app = FastAPI(title="Horizon Report API")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    add_routes(app, chain, path="/classify")
    return app
