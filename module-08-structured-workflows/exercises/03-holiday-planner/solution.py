"""
Exercise 03 — Holiday Planner FastAPI Backend (Solution)
=========================================================
A FastAPI app that uses plan-and-execute for holiday planning,
with MCP tools for flights, hotels, and preferences.

Run:  uvicorn solution:app --reload --port 8000
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
from solution_server import (
    search_web as mcp_search_web,
    remember_preference,
    recall_preferences,
    search_flights,
    search_hotels,
)

load_dotenv()

app = FastAPI(title="Holiday Planner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI()

_EXTRA_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "remember_preference",
            "description": "Store a user travel preference (e.g. budget, dietary needs, interests).",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Preference name"},
                    "value": {"type": "string", "description": "Preference value"},
                },
                "required": ["key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recall_preferences",
            "description": "Recall all stored user travel preferences.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": "Search for flights between two cities on a given date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "Departure city"},
                    "destination": {"type": "string", "description": "Arrival city"},
                    "date": {"type": "string", "description": "Travel date (YYYY-MM-DD)"},
                },
                "required": ["origin", "destination", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_hotels",
            "description": "Search for hotels in a location for given dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City or area"},
                    "checkin": {"type": "string", "description": "Check-in date (YYYY-MM-DD)"},
                    "checkout": {"type": "string", "description": "Check-out date (YYYY-MM-DD)"},
                },
                "required": ["location", "checkin", "checkout"],
            },
        },
    },
]


def register_mcp_tools() -> None:
    """Register MCP tool functions and schemas with the ReAct agent."""
    TOOLS["search_web"] = mcp_search_web
    TOOLS["remember_preference"] = remember_preference
    TOOLS["recall_preferences"] = recall_preferences
    TOOLS["search_flights"] = search_flights
    TOOLS["search_hotels"] = search_hotels

    existing_names = {s["function"]["name"] for s in TOOL_SCHEMAS}
    for schema in _EXTRA_SCHEMAS:
        if schema["function"]["name"] not in existing_names:
            TOOL_SCHEMAS.append(schema)


register_mcp_tools()


class MessageItem(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str | None = None
    messages: list[MessageItem] | None = None

    def user_message(self) -> str:
        if self.message:
            return self.message
        if self.messages:
            for m in reversed(self.messages):
                if m.role == "user":
                    return m.content
        return ""


def execute_plan_steps(plan: list[PlanStep], results: list[dict], client: OpenAI):
    """Execute each plan step via ReAct. Yields SSE event strings and appends to *results*."""
    for step in plan:
        step.status = "running"
        yield f"event: plan_step\ndata: {json.dumps({'number': step.step_number, 'description': step.description, 'status': 'running', 'result': None})}\n\n"

        try:
            react_result = execute_step(step, results, client)
            step.status = "done"
            step.result = react_result["answer"]
            results.append({
                "step_number": step.step_number,
                "description": step.description,
                "result": step.result,
            })
            yield f"event: plan_step\ndata: {json.dumps({'number': step.step_number, 'description': step.description, 'status': 'done', 'result': step.result})}\n\n"
        except Exception as e:
            step.status = "failed"
            step.result = str(e)
            yield f"event: plan_step\ndata: {json.dumps({'number': step.step_number, 'description': step.description, 'status': 'failed', 'result': str(e)})}\n\n"


def summarize_results(message: str, results: list[dict], client: OpenAI) -> str:
    """Compile step results into a final travel plan summary."""
    combined = "\n".join(f"Step {r['step_number']}: {r['result']}" for r in results)
    final = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a travel planning assistant. Summarize the research results "
                    "into a clear, well-organized holiday plan. Include specific recommendations "
                    "for flights, hotels, and activities where available."
                ),
            },
            {
                "role": "user",
                "content": f"Original request: {message}\n\nResearch results:\n{combined}",
            },
        ],
    )
    return final.choices[0].message.content or combined


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/preferences")
def preferences():
    """Return stored user travel preferences."""
    from solution_server import _preferences
    return dict(_preferences)


@app.post("/plan")
def create_plan(req: ChatRequest):
    """Generate a plan for the given message. Returns JSON with plan steps."""
    plan = generate_plan(req.user_message(), client)
    return {
        "plan": [
            {"step_number": s.step_number, "description": s.description}
            for s in plan
        ]
    }


@app.post("/chat")
def chat(req: ChatRequest):
    """Run plan-and-execute and stream results as SSE."""
    message = req.user_message()

    def sse_generator():
        plan = generate_plan(message, client)
        for s in plan:
            yield f"event: plan_step\ndata: {json.dumps({'number': s.step_number, 'description': s.description, 'status': 'pending', 'result': None})}\n\n"

        results: list[dict] = []
        yield from execute_plan_steps(plan, results, client)

        answer = summarize_results(message, results, client)
        yield f"event: done\ndata: {json.dumps({'role': 'assistant', 'content': answer})}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")
