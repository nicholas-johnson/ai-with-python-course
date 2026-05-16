"""Agentic conversation loop with tool calling.

This module implements the core agent loop:
1. Build a system prompt using the user's preferences
2. Send messages to OpenAI with tool definitions
3. When the model calls tools, execute them and feed results back
4. Repeat until the model returns a final text response
"""

import json
from typing import AsyncGenerator

import chromadb
from openai import OpenAI

from .config import OPENAI_MODEL, load_preferences
from .tools import (
    add_calendar_event,
    add_reminder,
    delete_calendar_event,
    get_calendar,
    get_reminders,
    get_weather,
    search_notes,
)

client = OpenAI()


# TODO: Define TOOL_DEFINITIONS — a list of OpenAI function tool schemas.
# Each tool needs: name, description, parameters (JSON Schema).
# Tools to define: search_notes, get_calendar, add_calendar_event,
#                  delete_calendar_event, get_reminders, add_reminder, get_weather
TOOL_DEFINITIONS = [
    # Example structure:
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "search_notes",
    #         "description": "Search through personal notes...",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "query": {"type": "string", "description": "The search query"},
    #             },
    #             "required": ["query"],
    #         },
    #     },
    # },
]


# Maps tool names to callable functions.
# Each lambda takes (args_dict, collection) and calls the right tool function.
TOOL_MAP = {
    "get_calendar": lambda args, col: get_calendar(args.get("date_range")),
    "add_calendar_event": lambda args, col: add_calendar_event(**args),
    "delete_calendar_event": lambda args, col: delete_calendar_event(args["event_id"]),
    "get_reminders": lambda args, col: get_reminders(),
    "add_reminder": lambda args, col: add_reminder(**args),
    "get_weather": lambda args, col: get_weather(args.get("city", "London")),
    "search_notes": lambda args, col: search_notes(args["query"], col),
}


def _build_system_prompt() -> str:
    """Build a personalised system prompt from preferences.json.

    Load preferences and construct a prompt like:
    "You are Compass, {name}'s personal AI assistant. You're friendly,
    helpful, and a little witty. {name} is interested in {interests}..."
    """
    prefs = load_preferences()
    # TODO: Extract name, interests, dietary info from prefs
    # TODO: Return a system prompt string
    return "You are a helpful personal assistant."


def run_assistant(
    message: str,
    history: list[dict],
    collection: chromadb.Collection,
    max_iterations: int = 5,
) -> str:
    """Run the assistant agent loop. Returns the final text response.

    Steps:
    1. Build messages list: system prompt + history + new user message
    2. Loop up to max_iterations:
       a. Call OpenAI chat completions with tools
       b. If finish_reason is "tool_calls":
          - Append the assistant message
          - Execute each tool call using TOOL_MAP
          - Append tool results as "tool" role messages
          - Continue the loop
       c. Otherwise, return the text content
    """
    messages = [{"role": "system", "content": _build_system_prompt()}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    # TODO: Implement the agent loop
    # Hint: response = client.chat.completions.create(
    #     model=OPENAI_MODEL, messages=messages, tools=TOOL_DEFINITIONS
    # )
    # Check choice.finish_reason == "tool_calls"

    return "Not yet implemented."


async def run_assistant_stream(
    message: str,
    history: list[dict],
    collection: chromadb.Collection,
    max_iterations: int = 5,
) -> AsyncGenerator[str, None]:
    """Run the assistant agent loop with streaming. Yields text chunks.

    Same logic as run_assistant, but:
    - Use stream=True in the API call
    - Yield delta.content chunks as they arrive
    - Accumulate tool_calls from deltas before executing
    """
    messages = [{"role": "system", "content": _build_system_prompt()}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    # TODO: Implement streaming agent loop
    # Hint: Use client.chat.completions.create(..., stream=True)
    # Iterate over chunks, yield content deltas, accumulate tool calls

    yield "Streaming not yet implemented."
