"""
Exercise 04 — Chain API (solution)
Run server:  uvicorn solution:create_app --factory --reload
Test:        pytest test_start.py -v
"""

from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

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

chain = prompt | ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0) | JsonOutputParser()


class ReportInput(BaseModel):
    report: str


class InvokeRequest(BaseModel):
    input: ReportInput


class BatchRequest(BaseModel):
    inputs: list[ReportInput]


def create_app() -> FastAPI:
    app = FastAPI(title="Horizon Report API")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/classify/invoke")
    async def classify_invoke(req: InvokeRequest) -> dict[str, Any]:
        return {"output": await chain.ainvoke(req.input.model_dump())}

    @app.post("/classify/batch")
    async def classify_batch(req: BatchRequest) -> dict[str, Any]:
        return {"output": await chain.abatch([i.model_dump() for i in req.inputs])}

    @app.post("/classify/stream")
    async def classify_stream(req: InvokeRequest) -> StreamingResponse:
        async def events():
            # JsonOutputParser yields the partial JSON object as it fills in.
            async for partial in chain.astream(req.input.model_dump()):
                yield json.dumps(partial) + "\n"

        return StreamingResponse(events(), media_type="application/x-ndjson")

    return app
