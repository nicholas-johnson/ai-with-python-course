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
    """Load destinations and build the search index.

    TODO:
    - Load destinations.json from DATA_DIR
    - Call build_index(destinations) to create the ChromaDB collection
    - Store both in the global variables
    """
    pass


@app.get("/api/health")
async def health():
    """Health check endpoint.

    TODO: Return dict with status, destinations_loaded count, index_ready bool
    """
    pass


@app.post("/api/plan")
async def plan(request: PlanRequest):
    """Generate a day-by-day travel itinerary using the agentic planner.

    TODO:
    1. Create a TraceContext
    2. Look up destination in destinations list (case-insensitive name match)
    3. If found, run check_safety — raise HTTPException(400) if unsafe
    4. Call plan_trip with request params and the collection
    5. Run validate_budget on the daily_plan
    6. Add budget_validation and trace to the response
    7. Return the itinerary
    """
    pass


@app.post("/api/search")
async def search(request: SearchRequest):
    """Search destinations by query.

    TODO:
    - Call search_destinations(query, collection, k=5)
    - Return {"results": ..., "trace": ...}
    """
    pass


@app.get("/api/destination/{dest_id}")
async def get_destination(dest_id: str):
    """Get full destination details by ID.

    TODO:
    - Find destination with matching id in destinations list
    - Raise HTTPException(404) if not found
    - Return the destination dict
    """
    pass


@app.get("/api/weather")
async def weather(city: str):
    """Get mock weather for a city.

    TODO: Return get_weather(city)
    """
    pass
