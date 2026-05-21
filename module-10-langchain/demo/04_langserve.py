"""
Demo 4: LangServe — deploy an LCEL chain as a REST API.
Run:  python module-10-langchain/demo/04_langserve.py

DSS Pathfinder: same classification chain as demo 01, exposed via FastAPI + LangServe.

Part 1: Build the chain (same as demo 01)
Part 2: Wire add_routes and inspect OpenAPI
Part 3: Call /classify/invoke via httpx (in-process, no separate server)
Part 4: uvicorn + playground instructions for live use

Requires: pip install -e ".[langchain]" and OPENAI_API_KEY for invoke/stream.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langserve import add_routes

load_dotenv()

MODEL = "gpt-4o-mini"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS = json.loads((PROJECT_ROOT / "data" / "ship_logs.json").read_text())
SAMPLE_REPORT = LOGS[0]["content"]

# ---------------------------------------------------------------------------
# Chain (same as demo 01)
# ---------------------------------------------------------------------------

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a ship incident classifier for the DSS Pathfinder.\n"
        "Classify the crew report into exactly one category: "
        "navigation, engineering, science, medical, or operations.\n"
        "Respond with ONLY a JSON object (no markdown fences) containing:\n"
        '  "category": one of the five categories,\n'
        '  "summary": a one-sentence summary,\n'
        '  "priority": one of low, medium, high, critical.',
    ),
    ("human", "{report}"),
])

chain = prompt | ChatOpenAI(model=MODEL, temperature=0) | JsonOutputParser()


def create_app() -> FastAPI:
    """FastAPI app with LangServe routes for the classification chain."""
    app = FastAPI(title="Pathfinder Report API")
    add_routes(app, chain, path="/classify")
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
    print("    chain = prompt | ChatOpenAI(...) | JsonOutputParser()\n")

    result = chain.invoke({"report": SAMPLE_REPORT})
    print(f"  Sample report: {SAMPLE_REPORT[:80]}...")
    print(f"  chain.invoke() → {json.dumps(result, indent=2)}\n")

    pause()


# ---------------------------------------------------------------------------
# Part 2: add_routes + OpenAPI
# ---------------------------------------------------------------------------

def demo_add_routes():
    print("=" * 60)
    print("PART 2: ADD_ROUTES + OPENAPI")
    print("=" * 60)

    app = create_app()
    schema = app.openapi()
    paths = sorted(schema["paths"].keys())

    print("\n  add_routes(app, chain, path='/classify') registers:\n")
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
    pause()


# ---------------------------------------------------------------------------
# Part 4: Run live server
# ---------------------------------------------------------------------------

def demo_run_server():
    print("=" * 60)
    print("PART 4: RUN LIVE (uvicorn + playground)")
    print("=" * 60)

    print("\n  Starting server on http://127.0.0.1:8000 ...")
    print("  Press Ctrl+C to stop.\n")
    print("  Try in another terminal or browser:\n")
    print("    OpenAPI docs:  http://127.0.0.1:8000/docs")
    print("    Playground:    http://127.0.0.1:8000/classify/playground/")
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
    "2": ("add_routes + OpenAPI", demo_add_routes),
    "3": ("HTTP invoke (httpx)", demo_http_invoke),
    "4": ("Run live (uvicorn)", demo_run_server),
}


def main():
    print("\n" + "=" * 60)
    print("  DEMO 4 — LANGSERVE")
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
    print("  chain = prompt | model | parser   — same as demo 01")
    print("  add_routes(app, chain, path='/classify')  — REST API in one line")
    print("  POST /classify/invoke  {\"input\": {\"report\": \"...\"}}")
    print("=" * 60)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        import uvicorn

        uvicorn.run(create_app, factory=True, host="127.0.0.1", port=8000, reload=True)
    else:
        main()
