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
from openai import OpenAI

from planner import generate_plan, execute_step, plan_and_execute, PlanStep
from react_agent import run_react

app = FastAPI(title="Holiday Planner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI()


class ChatRequest(BaseModel):
    message: str


# --- MCP tool imports ---
# TODO: Import tool functions from server.py and register them
# so the ReAct agent can use holiday-planning tools.
#
# from server import search_web, remember_preference, recall_preferences
# from server import search_flights, search_hotels
#
# Then add them to the react_agent TOOLS dict and TOOL_SCHEMAS list.


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
    """Run plan-and-execute and stream results as SSE."""
    # TODO: implement an SSE generator that:
    # 1. Generates a plan and yields: data: {"type": "plan", "steps": [...]}
    # 2. For each step, yields:
    #    data: {"type": "step_start", "step": N, "description": "..."}
    #    Then executes the step
    #    data: {"type": "step_done", "step": N, "result": "..."}
    # 3. Compiles final answer and yields:
    #    data: {"type": "answer", "content": "..."}
    #
    # return StreamingResponse(sse_generator(), media_type="text/event-stream")
    raise NotImplementedError("TODO")
