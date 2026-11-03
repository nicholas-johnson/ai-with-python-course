"""Shared tools and metering for the Module 8 workflow demos.

The four strategies in `01_control_flow.py` only produce a fair comparison if
they all reach for the same tools, so they live here rather than being copied
into each demo.

The ship tools sleep for `TOOL_LATENCY` seconds to stand in for a real network
call. Without that the parallel executor in `04_parallel_plan.py` has nothing
to overlap and the speed-up disappears into noise.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

TOOL_LATENCY = float(os.getenv("DEMO_TOOL_LATENCY", "0.8"))


# ---------------------------------------------------------------------------
# Metering
# ---------------------------------------------------------------------------

@dataclass
class Meter:
    """Counts what a strategy spent so the demos can compare like for like."""

    llm_calls: int = 0
    tool_calls: int = 0
    tokens: int = 0
    seconds: float = 0.0
    decisions: list[tuple[str, str]] = field(default_factory=list)

    def record_llm(self, response) -> None:
        self.llm_calls += 1
        usage = getattr(response, "usage", None)
        if usage is not None:
            self.tokens += getattr(usage, "total_tokens", 0) or 0

    def record_tool(self, name: str) -> None:
        self.tool_calls += 1

    def decide(self, who: str, what: str) -> None:
        """Log whether code or the model chose this step."""
        self.decisions.append((who, what))

    @property
    def model_decisions(self) -> int:
        return sum(1 for who, _ in self.decisions if who == "model")


class Timer:
    """Context manager that writes elapsed wall-clock onto a Meter."""

    def __init__(self, meter: Meter):
        self.meter = meter

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.meter.seconds = time.perf_counter() - self.start
        return False


# ---------------------------------------------------------------------------
# Ship tools - local, deterministic, deliberately slow
# ---------------------------------------------------------------------------

SYSTEMS = {
    "reactor": (
        "Reactor: 94% efficiency. Plasma conduit 7-B showing minor fluctuation, within tolerance."
    ),
    "navigation": "Navigation: Online. Course locked to Kepler-442 asteroid belt. ETA 41 hours.",
    "life_support": "Life support: Nominal. CO2 scrubbers at 97%. Atmosphere stable on all decks.",
    "shields": "Shields: 85% charge. Depleted by ion storm, recharging at 2% per hour.",
    "sensors": (
        "Sensors: Long-range array degraded to 60% after the ion storm. "
        "Maintenance scheduled 0800."
    ),
}

_notes: list[str] = []
_reports: list[dict] = []


def check_system(system: str) -> str:
    """Report the status of one ship system."""
    time.sleep(TOOL_LATENCY)
    unknown = f"Unknown system: {system}. Known: {', '.join(SYSTEMS)}"
    return SYSTEMS.get(system.lower().strip(), unknown)


def search_logs(query: str) -> str:
    """Search the ship's logs for entries matching a keyword."""
    time.sleep(TOOL_LATENCY)
    try:
        logs = json.loads((DATA_DIR / "ship_logs.json").read_text())
    except OSError as e:
        return f"Log store unavailable: {e}"

    terms = [t for t in re.split(r"\W+", query.lower()) if len(t) > 3]
    hits = [
        log
        for log in logs
        if any(t in log["content"].lower() or t in " ".join(log["tags"]).lower() for t in terms)
    ]
    if not hits:
        return f"No log entries matching '{query}'."
    return "\n".join(f"[{log['id']}] {log['author']}: {log['content']}" for log in hits[:4])


def lookup_mission(mission_id: str) -> str:
    """Look up a mission by ID."""
    time.sleep(TOOL_LATENCY)
    try:
        missions = json.loads((DATA_DIR / "missions.json").read_text())
    except OSError as e:
        return f"Mission store unavailable: {e}"

    for mission in missions:
        if mission["id"].lower() == mission_id.lower().strip():
            return json.dumps(mission)
    return f"No mission with ID {mission_id}."


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


def read_notes() -> str:
    """Read all saved notes."""
    if not _notes:
        return "No notes yet."
    return "\n".join(f"{i + 1}. {n}" for i, n in enumerate(_notes))


def file_report(title: str, content: str) -> str:
    """File an official report into the ship's record. This cannot be undone."""
    time.sleep(TOOL_LATENCY)
    _reports.append({"title": title, "content": content})
    return f"Report '{title}' filed to the permanent record (#{len(_reports)})."


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
        return text[:2000] if text else "No results found."
    except Exception as e:
        return f"Search error: {e}"


def reset_state() -> None:
    """Clear notes and reports between demo sections."""
    _notes.clear()
    _reports.clear()


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

TOOLS = {
    "check_system": check_system,
    "search_logs": search_logs,
    "lookup_mission": lookup_mission,
    "calculator": calculator,
    "take_note": take_note,
    "read_notes": read_notes,
    "file_report": file_report,
    "search_web": search_web,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "name": "check_system",
        "description": "Report the status of one ship system.",
        "parameters": {
            "type": "object",
            "properties": {
                "system": {
                    "type": "string",
                    "description": "One of: reactor, navigation, life_support, shields, sensors",
                }
            },
            "required": ["system"],
        },
    },
    {
        "type": "function",
        "name": "search_logs",
        "description": "Search the ship's logs for entries matching a keyword.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Keywords to search for"}},
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "lookup_mission",
        "description": "Look up a mission by ID, for example MSN-001.",
        "parameters": {
            "type": "object",
            "properties": {"mission_id": {"type": "string", "description": "Mission ID"}},
            "required": ["mission_id"],
        },
    },
    {
        "type": "function",
        "name": "calculator",
        "description": "Evaluate a mathematical expression. Returns the result.",
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
        "name": "read_notes",
        "description": "Read all saved notes.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "file_report",
        "description": "File a report into the ship's permanent record. Cannot be undone.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Report title"},
                "content": {"type": "string", "description": "Report body"},
            },
            "required": ["title", "content"],
        },
    },
    {
        "type": "function",
        "name": "search_web",
        "description": "Search the web for information. Returns a text summary.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query"}},
            "required": ["query"],
        },
    },
]


def schemas_for(*names: str) -> list[dict]:
    """Return the schemas for a subset of tools, keeping each agent's menu small."""
    wanted = set(names)
    return [s for s in TOOL_SCHEMAS if s["name"] in wanted]


def run_tool(name: str, arguments: str | dict, meter: Meter | None = None) -> str:
    """Dispatch a tool call, tolerating either raw JSON or a parsed dict."""
    args = json.loads(arguments) if isinstance(arguments, str) else arguments
    if meter is not None:
        meter.record_tool(name)
    fn = TOOLS.get(name)
    if fn is None:
        return f"Unknown tool: {name}"
    try:
        return str(fn(**args))
    except Exception as e:
        return f"Tool error in {name}: {e}"
