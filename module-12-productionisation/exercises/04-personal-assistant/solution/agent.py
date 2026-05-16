"""Agentic conversation loop with tool calling."""

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

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": "Search through personal notes using semantic search. Use when the user asks about something they've written down, a recipe, a meeting note, a plan, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_calendar",
            "description": "Get calendar events. Optionally filter by date or date range (format: 'YYYY-MM-DD' or 'YYYY-MM-DD:YYYY-MM-DD').",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_range": {
                        "type": "string",
                        "description": "Date or date range to filter, e.g. '2025-03-17' or '2025-03-17:2025-03-19'",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_calendar_event",
            "description": "Add a new event to the calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Event title"},
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "time": {"type": "string", "description": "Time in HH:MM format"},
                    "duration": {"type": "integer", "description": "Duration in minutes", "default": 60},
                    "location": {"type": "string", "description": "Event location", "default": ""},
                    "notes": {"type": "string", "description": "Additional notes", "default": ""},
                },
                "required": ["title", "date", "time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_calendar_event",
            "description": "Delete a calendar event by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "The event ID to delete"},
                },
                "required": ["event_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_reminders",
            "description": "Get all active (incomplete) reminders.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_reminder",
            "description": "Set a new reminder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "What to be reminded about"},
                    "due_date": {"type": "string", "description": "Due date in YYYY-MM-DD format"},
                    "due_time": {"type": "string", "description": "Due time in HH:MM format", "default": "09:00"},
                },
                "required": ["text", "due_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name", "default": "London"},
                },
            },
        },
    },
]

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
    prefs = load_preferences()
    name = prefs.get("name", "there")
    interests = ", ".join(prefs.get("interests", []))
    dietary = ", ".join(prefs.get("dietary_restrictions", []))
    cuisines = ", ".join(prefs.get("favourite_cuisines", []))

    return (
        f"You are Compass, {name}'s personal AI assistant. "
        f"You're friendly, helpful, and a little witty. "
        f"{name} is interested in {interests}. "
        f"They are {dietary} and enjoy {cuisines} cuisine. "
        f"Use their calendar, notes, and reminders to be proactively helpful. "
        f"When you use tools, summarise results in a natural, conversational way. "
        f"Keep responses concise but warm."
    )


def run_assistant(
    message: str,
    history: list[dict],
    collection: chromadb.Collection,
    max_iterations: int = 5,
) -> str:
    """Run the assistant agent loop. Returns the final text response."""
    messages = [{"role": "system", "content": _build_system_prompt()}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
        )

        choice = response.choices[0]

        if choice.finish_reason == "tool_calls":
            messages.append(choice.message)
            for tool_call in choice.message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                handler = TOOL_MAP.get(fn_name)
                if handler:
                    result = handler(fn_args, collection)
                else:
                    result = f"Unknown tool: {fn_name}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
        else:
            return choice.message.content or ""

    return "I got a bit lost in thought there — could you rephrase that?"


async def run_assistant_stream(
    message: str,
    history: list[dict],
    collection: chromadb.Collection,
    max_iterations: int = 5,
) -> AsyncGenerator[str, None]:
    """Run the assistant agent loop with streaming. Yields text chunks."""
    messages = [{"role": "system", "content": _build_system_prompt()}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    for _ in range(max_iterations):
        stream = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            stream=True,
        )

        collected_content = ""
        tool_calls_by_index: dict[int, dict] = {}
        finish_reason = None

        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue

            finish_reason = chunk.choices[0].finish_reason

            if delta.content:
                collected_content += delta.content
                yield delta.content

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_by_index:
                        tool_calls_by_index[idx] = {
                            "id": tc.id or "",
                            "function": {"name": "", "arguments": ""},
                        }
                    entry = tool_calls_by_index[idx]
                    if tc.id:
                        entry["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            entry["function"]["name"] += tc.function.name
                        if tc.function.arguments:
                            entry["function"]["arguments"] += tc.function.arguments

        if not tool_calls_by_index:
            return

        from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageToolCall
        from openai.types.chat.chat_completion_message_tool_call import Function

        reconstructed_calls = []
        for idx in sorted(tool_calls_by_index):
            tc_data = tool_calls_by_index[idx]
            reconstructed_calls.append(
                ChatCompletionMessageToolCall(
                    id=tc_data["id"],
                    type="function",
                    function=Function(
                        name=tc_data["function"]["name"],
                        arguments=tc_data["function"]["arguments"],
                    ),
                )
            )

        assistant_msg = ChatCompletionMessage(
            role="assistant",
            content=collected_content or None,
            tool_calls=reconstructed_calls,
        )
        messages.append(assistant_msg)

        for tc in reconstructed_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)

            handler = TOOL_MAP.get(fn_name)
            result = handler(fn_args, collection) if handler else f"Unknown tool: {fn_name}"

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    yield "\n\nI got a bit lost in thought there — could you rephrase that?"
