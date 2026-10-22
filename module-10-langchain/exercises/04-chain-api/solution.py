"""
Exercise 04 — Chain API (solution)
Run server:  uvicorn solution:create_app --factory --reload
Test:        pytest test_start.py -v
"""

from __future__ import annotations

import json
import os
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


class Classification(BaseModel):
    """Classification of a crew report."""

    category: Literal["navigation", "engineering", "science", "medical", "operations"]
    summary: str = Field(description="One-sentence summary of the report")
    priority: Literal["low", "medium", "high", "critical"]


prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a ship incident classifier for the CSS Horizon.\n"
        "Classify the crew report: pick the category, write a one-sentence "
        "summary, and set the priority.",
    ),
    ("human", "{report}"),
])

model = ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0)
chain = prompt | model.with_structured_output(Classification)

# Structured output arrives as one complete object, so the streaming route uses
# a JSON-parser chain, which yields the partial dict as it fills in.
stream_chain = (
    prompt
    + ("system", 'Respond with ONLY a JSON object with keys "category", "summary", "priority".')
    | model
    | JsonOutputParser()
)


class ReportInput(BaseModel):
    report: str


class InvokeRequest(BaseModel):
    input: ReportInput


class InvokeResponse(BaseModel):
    output: Classification


class BatchRequest(BaseModel):
    inputs: list[ReportInput]


class BatchResponse(BaseModel):
    output: list[Classification]


def create_app() -> FastAPI:
    app = FastAPI(title="Horizon Report API")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/classify/invoke")
    async def classify_invoke(req: InvokeRequest) -> InvokeResponse:
        return InvokeResponse(output=await chain.ainvoke(req.input.model_dump()))

    @app.post("/classify/batch")
    async def classify_batch(req: BatchRequest) -> BatchResponse:
        return BatchResponse(output=await chain.abatch([i.model_dump() for i in req.inputs]))

    @app.post("/classify/stream")
    async def classify_stream(req: InvokeRequest) -> StreamingResponse:
        async def events():
            async for partial in stream_chain.astream(req.input.model_dump()):
                yield json.dumps(partial) + "\n"

        return StreamingResponse(events(), media_type="application/x-ndjson")

    return app
