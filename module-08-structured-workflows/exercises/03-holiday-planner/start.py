"""
Exercise 03 — Holiday Planner FastAPI Backend (scaffold)
=========================================================
A FastAPI app that uses plan-and-execute for holiday planning.

Run:  uvicorn start:app --reload --port 8000
"""
from __future__ import annotations
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

from planner import generate_plan, execute_step, PlanStep
from react_agent import run_react, TOOLS, TOOL_SCHEMAS

load_dotenv()

app = FastAPI(title="Holiday Planner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI()


# --- MCP tool schemas (provided) ---
_EXTRA_SCHEMAS = [
    # TODO: Define OpenAI-format tool schemas for:
    #   remember_preference, recall_preferences, search_flights, search_hotels
    # Each needs: {"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}
]


def register_mcp_tools() -> None:
    """Register MCP tool functions and schemas with the ReAct agent.

    Steps:
        1. Import tool functions from server.py (search_web, remember_preference, etc.)
        2. Add each to the react_agent TOOLS dict
        3. Merge _EXTRA_SCHEMAS into TOOL_SCHEMAS (skip duplicates)
    """
    # TODO: implement
    raise NotImplementedError("TODO")


class ChatRequest(BaseModel):
    message: str


def execute_plan_steps(plan: list[PlanStep], results: list[dict], client: OpenAI):
    """Execute each plan step via ReAct. Yields SSE event strings and appends to *results*.

    For each step:
        1. Set step.status = "running", yield a step_start event
        2. Call execute_step(step, results, client)
        3. On success: set status/result, append to results, yield step_done
        4. On failure: set status/result, yield step_failed
    """
    # TODO: implement
    raise NotImplementedError("TODO")


def summarize_results(message: str, results: list[dict], client: OpenAI) -> str:
    """Compile step results into a final travel plan summary.

    Combine all step results and ask the LLM to produce a well-organized
    holiday plan with specific recommendations.
    """
    # TODO: implement
    raise NotImplementedError("TODO")


@app.get("/health")
def health():
    """Health check endpoint."""
    # TODO: return {"status": "ok"}
    raise NotImplementedError("TODO")


@app.post("/plan")
def create_plan(req: ChatRequest):
    """Generate a plan for the given message. Returns JSON with plan steps."""
    # TODO: call generate_plan(req.message, client)
    # Return {"plan": [{"step_number": ..., "description": ...}, ...]}
    raise NotImplementedError("TODO")


@app.post("/chat")
def chat(req: ChatRequest):
    """Run plan-and-execute and stream results as SSE.

    Build an sse_generator that:
        1. Generates a plan and yields a plan event
        2. Calls execute_plan_steps() and yields all step events
        3. Calls summarize_results() and yields the final answer event
    """
    # TODO: implement
    raise NotImplementedError("TODO")
