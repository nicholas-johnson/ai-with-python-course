"""FastAPI backend for the AI Travel Planner."""

import json
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import DATA_DIR
from .rag import build_index, search_destinations
from .agent import plan_trip
from .tools import get_weather
from .guardrails import validate_budget, check_safety
from .tracing import TraceContext

app = FastAPI(title="AI Travel Planner")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

destinations: list[dict] = []
collection = None


class PlanRequest(BaseModel):
    destination: str
    duration_days: int
    interests: list[str]
    budget: str = "moderate"


class SearchRequest(BaseModel):
    query: str


@app.on_event("startup")
async def startup():
    global destinations, collection
    data_path = os.path.join(DATA_DIR, "destinations.json")
    with open(data_path) as f:
        destinations = json.load(f)
    collection = build_index(destinations)


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "destinations_loaded": len(destinations),
        "index_ready": collection is not None,
    }


@app.post("/api/plan")
async def plan(request: PlanRequest):
    trace = TraceContext()
    span = trace.start_span("plan_endpoint")

    dest_data = next((d for d in destinations if d["name"].lower() == request.destination.lower()), None)
    if dest_data:
        safety = check_safety(dest_data)
        if not safety["safe"]:
            trace.end_span(span, status="blocked")
            raise HTTPException(status_code=400, detail=f"Safety advisory: {safety['advisories']}")

    itinerary = plan_trip(
        destination=request.destination,
        duration_days=request.duration_days,
        interests=request.interests,
        budget=request.budget,
        collection=collection,
    )

    budget_check = validate_budget(itinerary.get("daily_plan", []), request.budget)
    itinerary["budget_validation"] = budget_check

    trace.end_span(span)
    itinerary["request_trace"] = trace.summary()
    return itinerary


@app.post("/api/search")
async def search(request: SearchRequest):
    trace = TraceContext()
    span = trace.start_span("search_endpoint")

    results = search_destinations(request.query, collection, k=5)

    trace.end_span(span, metadata={"num_results": len(results)})
    return {"results": results, "trace": trace.summary()}


@app.get("/api/destination/{dest_id}")
async def get_destination(dest_id: str):
    dest = next((d for d in destinations if d["id"] == dest_id), None)
    if not dest:
        raise HTTPException(status_code=404, detail="Destination not found")
    return dest


@app.get("/api/weather")
async def weather(city: str):
    return get_weather(city)
