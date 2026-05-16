"""Agentic travel planning — iterative research and itinerary building."""

import json

from openai import OpenAI
import chromadb

from .config import OPENAI_MODEL
from .tools import get_weather, estimate_budget, estimate_travel_time
from .rag import search_attractions
from .tracing import TraceContext

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
    """Execute a tool call and return the result as JSON string."""
    if name == "search_attractions":
        results = search_attractions(args["query"], args["dest_id"], collection)
        return json.dumps(results[:5])
    elif name == "get_weather":
        return json.dumps(get_weather(args["city"]))
    elif name == "estimate_budget":
        return json.dumps(estimate_budget(args["activities"], args["budget_level"]))
    elif name == "estimate_travel_time":
        return json.dumps(estimate_travel_time(args["from_loc"], args["to_loc"]))
    return json.dumps({"error": f"Unknown tool: {name}"})


def plan_trip(
    destination: str,
    duration_days: int,
    interests: list[str],
    budget: str,
    collection: chromadb.Collection,
) -> dict:
    """Plan a trip using an agentic loop with tool calls."""
    trace = TraceContext()
    span = trace.start_span("plan_trip")

    system_prompt = f"""You are an expert travel planner. Create a detailed day-by-day itinerary.

Destination: {destination}
Duration: {duration_days} days
Interests: {', '.join(interests)}
Budget level: {budget}

Use the available tools to:
1. Search for attractions matching the traveller's interests
2. Check the weather forecast
3. Estimate costs for each day
4. Estimate travel times between locations

Then produce a JSON itinerary with this structure:
{{
  "destination": "{destination}",
  "duration_days": {duration_days},
  "budget_level": "{budget}",
  "daily_plan": [
    {{
      "day": 1,
      "theme": "...",
      "activities": ["...", "..."],
      "estimated_cost_usd": 0,
      "notes": "..."
    }}
  ],
  "tips": ["...", "..."],
  "total_estimated_cost_usd": 0
}}

Research thoroughly, then return ONLY the JSON."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Plan my {duration_days}-day trip to {destination}. I'm interested in {', '.join(interests)} on a {budget} budget."},
    ]

    max_iterations = 8
    for iteration in range(max_iterations):
        iter_span = trace.start_span(f"llm_call_{iteration}")

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto" if iteration < max_iterations - 1 else "none",
        )

        message = response.choices[0].message
        messages.append(message)
        trace.end_span(iter_span, metadata={"finish_reason": response.choices[0].finish_reason})

        if not message.tool_calls:
            break

        for tool_call in message.tool_calls:
            tool_span = trace.start_span(f"tool_{tool_call.function.name}")
            args = json.loads(tool_call.function.arguments)
            result = _execute_tool(tool_call.function.name, args, collection)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })
            trace.end_span(tool_span, metadata={"args": args})

    trace.end_span(span, metadata={"iterations": iteration + 1})

    content = message.content or ""
    try:
        start = content.index("{")
        end = content.rindex("}") + 1
        itinerary = json.loads(content[start:end])
    except (ValueError, json.JSONDecodeError):
        itinerary = {
            "destination": destination,
            "duration_days": duration_days,
            "budget_level": budget,
            "daily_plan": [],
            "tips": [],
            "total_estimated_cost_usd": 0,
            "raw_response": content,
        }

    itinerary["trace"] = trace.summary()
    return itinerary
