"""Tool implementations for the personal assistant agent."""

import json
import os
import uuid
from datetime import datetime

import chromadb

from .config import DATA_DIR
from .rag import search_notes as _rag_search


def search_notes(query: str, collection: chromadb.Collection) -> str:
    """RAG search over embedded notes."""
    hits = _rag_search(query, collection, k=5)
    if not hits:
        return "No matching notes found."
    lines = []
    for h in hits:
        lines.append(f"- **{h['title']}** (tags: {h['tags']})\n  {h['content'][:200]}")
    return "\n".join(lines)


def get_calendar(date_range: str | None = None) -> str:
    """Read upcoming events from calendar.json. Optional date_range like '2025-03-17' or '2025-03-17:2025-03-19'."""
    path = os.path.join(DATA_DIR, "calendar.json")
    with open(path) as f:
        events = json.load(f)

    if date_range:
        parts = date_range.split(":")
        start_date = parts[0].strip()
        end_date = parts[1].strip() if len(parts) > 1 else start_date
        events = [e for e in events if start_date <= e["date"] <= end_date]

    if not events:
        return "No events found for that date range."

    lines = []
    for e in events:
        loc = f" @ {e['location']}" if e.get("location") else ""
        lines.append(f"- {e['date']} {e['time']} — {e['title']}{loc} ({e['duration_minutes']}min)")
        if e.get("notes"):
            lines.append(f"  Notes: {e['notes']}")
    return "\n".join(lines)


def add_calendar_event(
    title: str,
    date: str,
    time: str,
    duration: int = 60,
    location: str = "",
    notes: str = "",
) -> str:
    """Add a new event to calendar.json."""
    path = os.path.join(DATA_DIR, "calendar.json")
    with open(path) as f:
        events = json.load(f)

    event_id = f"event-{uuid.uuid4().hex[:6]}"
    new_event = {
        "id": event_id,
        "title": title,
        "date": date,
        "time": time,
        "duration_minutes": duration,
        "location": location,
        "notes": notes,
    }
    events.append(new_event)
    events.sort(key=lambda e: (e["date"], e["time"]))

    with open(path, "w") as f:
        json.dump(events, f, indent=2)

    return f"Added '{title}' on {date} at {time} (id: {event_id})"


def delete_calendar_event(event_id: str) -> str:
    """Remove an event from calendar.json by ID."""
    path = os.path.join(DATA_DIR, "calendar.json")
    with open(path) as f:
        events = json.load(f)

    original_count = len(events)
    events = [e for e in events if e["id"] != event_id]

    if len(events) == original_count:
        return f"No event found with id '{event_id}'."

    with open(path, "w") as f:
        json.dump(events, f, indent=2)

    return f"Deleted event '{event_id}'."


def get_reminders() -> str:
    """Read active reminders from reminders.json."""
    path = os.path.join(DATA_DIR, "reminders.json")
    with open(path) as f:
        reminders = json.load(f)

    active = [r for r in reminders if not r.get("completed")]
    if not active:
        return "No active reminders."

    lines = []
    for r in active:
        recurring = " (recurring)" if r.get("recurring") else ""
        lines.append(f"- {r['due_date']} {r['due_time']} — {r['text']}{recurring}")
    return "\n".join(lines)


def add_reminder(text: str, due_date: str, due_time: str = "09:00") -> str:
    """Add a new reminder to reminders.json."""
    path = os.path.join(DATA_DIR, "reminders.json")
    with open(path) as f:
        reminders = json.load(f)

    reminder_id = f"reminder-{uuid.uuid4().hex[:6]}"
    new_reminder = {
        "id": reminder_id,
        "text": text,
        "due_date": due_date,
        "due_time": due_time,
        "recurring": False,
        "completed": False,
    }
    reminders.append(new_reminder)

    with open(path, "w") as f:
        json.dump(reminders, f, indent=2)

    return f"Reminder set: '{text}' for {due_date} at {due_time}"


def get_weather(city: str = "London") -> str:
    """Mock weather API — returns simulated weather data."""
    forecasts = {
        "London": {"temp": 14, "condition": "Partly cloudy", "wind": "12 mph SW"},
        "Manchester": {"temp": 11, "condition": "Light rain", "wind": "15 mph W"},
        "Edinburgh": {"temp": 9, "condition": "Overcast", "wind": "18 mph NW"},
    }
    data = forecasts.get(city, {"temp": 13, "condition": "Mostly sunny", "wind": "10 mph"})
    return f"Weather in {city}: {data['condition']}, {data['temp']}°C, wind {data['wind']}"
