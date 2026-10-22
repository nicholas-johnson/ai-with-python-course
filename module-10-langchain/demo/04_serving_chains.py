"""
Demo 4: Serving chains — deploy an LCEL chain as a REST API with FastAPI.
Run:  python module-10-langchain/demo/04_serving_chains.py

DSS Pathfinder: same classification chain as demo 01, exposed via FastAPI routes
that call the chain's async Runnable methods (ainvoke / abatch / astream).

Part 1: Build the chain (same as demo 01)
Part 2: Wire the routes and inspect OpenAPI
Part 3: Call /classify/invoke via httpx (in-process, no separate server)
Part 4: Run live with uvicorn

Requires: pip install -e ".[langchain]" and OPENAI_API_KEY for invoke/stream.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Literal

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS = json.loads((PROJECT_ROOT / "data" / "ship_logs.json").read_text())
SAMPLE_REPORT = LOGS[0]["content"]

# ---------------------------------------------------------------------------
# Chain (same as demo 01)
# ---------------------------------------------------------------------------

class Classification(BaseModel):
    """Classification of a crew report."""

    category: Literal["navigation", "engineering", "science", "medical", "operations"]
    summary: str = Field(description="One-sentence summary of the report")
    priority: Literal["low", "medium", "high", "critical"]


prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a ship incident classifier for the DSS Pathfinder.\n"
        "Classify the crew report: pick the category, write a one-sentence "
        "summary, and set the priority.",
    ),
    ("human", "{report}"),
])

model = ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0, use_responses_api=True)
chain = prompt | model.with_structured_output(Classification)

# Structured output arrives in one piece; for token-by-token streaming use a
# JSON-parser chain, which yields the partial dict as it fills in.
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
    """FastAPI app exposing the classification chain's invoke / batch / stream."""
    app = FastAPI(title="Pathfinder Report API")

    @app.post("/classify/invoke")
    async def classify_invoke(req: InvokeRequest) -> InvokeResponse:
        return InvokeResponse(output=await chain.ainvoke(req.input.model_dump()))

    @app.post("/classify/batch")
    async def classify_batch(req: BatchRequest) -> BatchResponse:
        return BatchResponse(output=await chain.abatch([i.model_dump() for i in req.inputs]))

    @app.post("/classify/stream")
    async def classify_stream(req: InvokeRequest):
        async def events():
            async for partial in stream_chain.astream(req.input.model_dump()):
                yield json.dumps(partial) + "\n"

        return StreamingResponse(events(), media_type="application/x-ndjson")

    return app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pause():
    try:
        input("\n  [Press Enter to continue...]\n")
    except (EOFError, KeyboardInterrupt):
        print()


# ---------------------------------------------------------------------------
# Part 1: Build the chain
# ---------------------------------------------------------------------------

def demo_build_chain():
    print("=" * 60)
    print("PART 1: BUILD THE CHAIN")
    print("=" * 60)

    print("\n  Same LCEL chain as demo 01:")
    print("    chain = prompt | model.with_structured_output(Classification)\n")

    result = chain.invoke({"report": SAMPLE_REPORT})
    print(f"  Sample report: {SAMPLE_REPORT[:80]}...")
    print(f"  chain.invoke() → {result!r}\n")

    pause()


# ---------------------------------------------------------------------------
# Part 2: Routes + OpenAPI
# ---------------------------------------------------------------------------

def demo_routes():
    print("=" * 60)
    print("PART 2: ROUTES + OPENAPI")
    print("=" * 60)

    app = create_app()
    schema = app.openapi()
    paths = sorted(schema["paths"].keys())

    print("\n  Three thin routes over the chain's Runnable methods:\n")
    for path in paths:
        if path.startswith("/classify"):
            methods = ", ".join(schema["paths"][path].keys()).upper()
            print(f"    {methods:12} {path}")

    print("\n  Full API docs at http://127.0.0.1:8000/docs when running uvicorn.\n")

    pause()


# ---------------------------------------------------------------------------
# Part 3: httpx in-process invoke
# ---------------------------------------------------------------------------

async def _invoke_via_http(report: str) -> dict:
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/classify/invoke",
            json={"input": {"report": report}},
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()


def demo_http_invoke():
    print("=" * 60)
    print("PART 3: HTTP INVOKE (httpx + ASGITransport)")
    print("=" * 60)

    print(f"\n  POST /classify/invoke")
    print(f'  Body: {{"input": {{"report": "..."}}}}\n')
    print(f"  Report: {SAMPLE_REPORT[:80]}...\n")

    try:
        payload = asyncio.run(_invoke_via_http(SAMPLE_REPORT))
        output = payload.get("output", payload)
        print(f"  Response output: {json.dumps(output, indent=2)}\n")
    except Exception as e:
        print(f"  Error (need OPENAI_API_KEY?): {e}\n")

    print("  No separate uvicorn process — httpx talks to the app in-memory.")
    print("  Note: LangServe's add_routes used to generate these routes; it is no")
    print("  longer maintained, and writing them yourself is only a few lines.")
    pause()


# ---------------------------------------------------------------------------
# Part 4: Run live server
# ---------------------------------------------------------------------------

def demo_run_server():
    print("=" * 60)
    print("PART 4: RUN LIVE (uvicorn)")
    print("=" * 60)

    print("\n  Starting server on http://127.0.0.1:8000 ...")
    print("  Press Ctrl+C to stop.\n")
    print("  Try in another terminal or browser:\n")
    print("    OpenAPI docs:  http://127.0.0.1:8000/docs")
    print("\n  curl example:\n")
    print('    curl -X POST http://127.0.0.1:8000/classify/invoke \\')
    print('      -H "Content-Type: application/json" \\')
    print(f'      -d \'{{"input": {{"report": "{SAMPLE_REPORT[:40]}..."}}}}\'\n')

    import uvicorn

    uvicorn.run(create_app, factory=True, host="127.0.0.1", port=8000)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DEMOS = {
    "1": ("Build the chain", demo_build_chain),
    "2": ("Routes + OpenAPI", demo_routes),
    "3": ("HTTP invoke (httpx)", demo_http_invoke),
    "4": ("Run live (uvicorn)", demo_run_server),
}


def main():
    print("\n" + "=" * 60)
    print("  DEMO 4 — SERVING CHAINS")
    print("=" * 60)

    while True:
        print("\nPick a section:\n")
        for key, (label, _) in DEMOS.items():
            print(f"  {key}. {label}")
        print("  q. Quit\n")

        try:
            choice = input("Enter choice> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice in ("q", "quit", ""):
            break
        elif choice in DEMOS:
            _, fn = DEMOS[choice]
            print()
            fn()
        else:
            print(f"Unknown option: {choice}")

    print("\n" + "=" * 60)
    print("RECAP")
    print("=" * 60)
    print()
    print("  chain = prompt | model.with_structured_output(...)  — same as demo 01")
    print("  await chain.ainvoke(...) inside a FastAPI route — REST API")
    print("  chain.astream(...) + StreamingResponse         — streaming")
    print("  POST /classify/invoke  {\"input\": {\"report\": \"...\"}}")
    print("=" * 60)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        import uvicorn

        uvicorn.run(create_app, factory=True, host="127.0.0.1", port=8000, reload=True)
    else:
        main()
