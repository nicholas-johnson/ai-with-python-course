"""Provided for Exercise 03: the tools, and a single-step executor.

You do not need to change anything in here. Your job is the scheduling, the
approval gate, and the checkpoint in `start.py`.

Note `book_flight`: it is irreversible, which is the whole reason the approval
gate exists. Each tool sleeps briefly so that running steps concurrently is
visibly faster than running them one at a time.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time

import httpx
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

TOOL_LATENCY = float(os.getenv("EXERCISE_TOOL_LATENCY", "0.6"))

# Tools that cannot be undone. The approval gate is keyed off this set - and it
# lives in code on purpose. A plan that could mark its own steps as safe would
# not be a safety control.
IRREVERSIBLE = {"book_flight"}

_notes: list[str] = []
_bookings: list[str] = []

DESTINATIONS = {
    "lisbon": (
        "Lisbon: 22C in May, flights from GBP 90, highlights: Alfama, Belem, Sintra."
    ),
    "reykjavik": (
        "Reykjavik: 9C in May, flights from GBP 150, highlights: Blue Lagoon, Golden Circle."
    ),
    "palermo": (
        "Palermo: 24C in May, flights from GBP 110, highlights: street food, Monreale."
    ),
    "tallinn": (
        "Tallinn: 14C in May, flights from GBP 80, highlights: old town, Kadriorg, Lahemaa."
    ),
}

FLIGHTS = {
    "lisbon": "FR1823 LGW-LIS 07:10, GBP 94",
    "reykjavik": "FI451 LHR-KEF 13:40, GBP 162",
    "palermo": "W64321 STN-PMO 06:25, GBP 108",
    "tallinn": "BT652 LGW-TLL 11:05, GBP 83",
}


def research_destination(city: str) -> str:
    """Look up weather, cost and highlights for a destination."""
    time.sleep(TOOL_LATENCY)
    return DESTINATIONS.get(city.lower().strip(), f"No guide for {city}.")


def find_flight(city: str) -> str:
    """Find the cheapest flight to a city. Does not book anything."""
    time.sleep(TOOL_LATENCY)
    return FLIGHTS.get(city.lower().strip(), f"No flights found to {city}.")


def book_flight(flight_id: str) -> str:
    """Book a flight. This spends money and cannot be undone."""
    time.sleep(TOOL_LATENCY)
    _bookings.append(flight_id)
    return f"BOOKED {flight_id}. Confirmation #{1000 + len(_bookings)}."


def calculator(expression: str) -> str:
    """Evaluate a mathematical expression safely."""
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return "Error: only digits and basic operators allowed"
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"Error: {e}"


def take_note(content: str) -> str:
    """Save a note for later reference."""
    _notes.append(content)
    return f"Note saved ({len(_notes)} total)."


def search_web(query: str) -> str:
    """Search the web for information."""
    try:
        resp = httpx.get(
            "https://lite.duckduckgo.com/lite",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        text = re.sub(r"<[^>]+>", " ", resp.text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:1500] if text else "No results found."
    except Exception as e:
        return f"Search error: {e}"


TOOLS = {
    "research_destination": research_destination,
    "find_flight": find_flight,
    "book_flight": book_flight,
    "calculator": calculator,
    "take_note": take_note,
    "search_web": search_web,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "name": "research_destination",
        "description": "Look up weather, cost and highlights for a destination city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "City name"}},
            "required": ["city"],
        },
    },
    {
        "type": "function",
        "name": "find_flight",
        "description": "Find the cheapest flight to a city. Does not book anything.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "City name"}},
            "required": ["city"],
        },
    },
    {
        "type": "function",
        "name": "book_flight",
        "description": "Book a flight by its ID. Spends money and cannot be undone.",
        "parameters": {
            "type": "object",
            "properties": {"flight_id": {"type": "string", "description": "Flight ID"}},
            "required": ["flight_id"],
        },
    },
    {
        "type": "function",
        "name": "calculator",
        "description": "Evaluate a mathematical expression.",
        "parameters": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "Math expression"}},
            "required": ["expression"],
        },
    },
    {
        "type": "function",
        "name": "take_note",
        "description": "Save a note for later reference.",
        "parameters": {
            "type": "object",
            "properties": {"content": {"type": "string", "description": "Note content"}},
            "required": ["content"],
        },
    },
    {
        "type": "function",
        "name": "search_web",
        "description": "Search the web for information.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query"}},
            "required": ["query"],
        },
    },
]


def run_tool(name: str, arguments: str | dict) -> str:
    """Dispatch one tool call."""
    args = json.loads(arguments) if isinstance(arguments, str) else arguments
    fn = TOOLS.get(name)
    if fn is None:
        return f"Unknown tool: {name}"
    try:
        return str(fn(**args))
    except Exception as e:
        return f"Tool error in {name}: {e}"


async def execute_step(description: str, context: str, client: AsyncOpenAI) -> str:
    """Run one plan step as a small tool-calling agent. Provided for you."""
    messages = [
        {
            "role": "system",
            "content": "Carry out this one step using the tools. Reply with a concise result.",
        },
        {"role": "user", "content": f"{description}\n\n{context}".strip()},
    ]

    for _ in range(3):
        response = await client.responses.create(
            model=MODEL,
            reasoning={"effort": "none"},
            input=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            return response.output_text or "(no result)"

        messages += response.output
        for call in calls:
            # Blocking tool, so keep it off the event loop or the whole wave
            # serialises behind it.
            result = await asyncio.to_thread(run_tool, call.name, call.arguments)
            messages.append(
                {"type": "function_call_output", "output": result, "call_id": call.call_id}
            )
    return "(step did not finish)"


def reset_state() -> None:
    """Clear notes and bookings. Useful between runs."""
    _notes.clear()
    _bookings.clear()
