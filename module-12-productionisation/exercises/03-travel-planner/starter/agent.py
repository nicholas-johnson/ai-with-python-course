"""Agentic travel planning — iterative research and itinerary building."""

import json

from openai import OpenAI
import chromadb

from .config import OPENAI_MODEL
from .tools import get_weather, estimate_budget, estimate_travel_time
from .rag import search_attractions

client = OpenAI()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_attractions",
            "description": "Search for attractions and activities at a destination matching a query",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to search for (e.g. 'museums', 'outdoor hiking')"},
                    "dest_id": {"type": "string", "description": "Destination ID to search within"},
                },
                "required": ["query", "dest_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather and 5-day forecast for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_budget",
            "description": "Estimate daily costs for a list of planned activities",
            "parameters": {
                "type": "object",
                "properties": {
                    "activities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of planned activities for the day",
                    },
                    "budget_level": {
                        "type": "string",
                        "enum": ["budget", "moderate", "luxury"],
                        "description": "Traveller's budget level",
                    },
                },
                "required": ["activities", "budget_level"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_travel_time",
            "description": "Estimate travel time between two locations in a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_loc": {"type": "string", "description": "Starting location"},
                    "to_loc": {"type": "string", "description": "Destination location"},
                },
                "required": ["from_loc", "to_loc"],
            },
        },
    },
]


def _execute_tool(name: str, args: dict, collection: chromadb.Collection) -> str:
    """Execute a tool call and return the result as JSON string.

    TODO:
    - Match tool name to the appropriate function
    - Call search_attractions, get_weather, estimate_budget, or estimate_travel_time
    - Return JSON-serialized result
    - Return error JSON for unknown tools
    """
    pass


def plan_trip(
    destination: str,
    duration_days: int,
    interests: list[str],
    budget: str,
    collection: chromadb.Collection,
) -> dict:
    """Plan a trip using an agentic loop with tool calls.

    TODO:
    1. Create a TraceContext and start a span
    2. Build a system prompt instructing the LLM to plan a trip with:
       - destination, duration, interests, budget info
       - Instructions to use tools for research
       - Expected JSON output format for the itinerary
    3. Create initial messages list with system + user messages
    4. Agentic loop (max 8 iterations):
       a. Call client.chat.completions.create with messages, tools, tool_choice="auto"
       b. Append assistant message to messages
       c. If no tool_calls, break
       d. For each tool_call: parse args, call _execute_tool, append tool result message
    5. Parse the final response as JSON (find first { to last })
    6. Add trace summary to the result
    7. Return the itinerary dict
    """
    pass
