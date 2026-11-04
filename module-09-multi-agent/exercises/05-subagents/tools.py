"""
Provided scaffolding for Exercise 05 — Spawned Subagents.

Mock department archives, the two tool schemas (one for subagents, one for the
lead), the prompts, and the data shapes that cross the parent/child boundary.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

DEPARTMENTS = ["medical", "logistics", "tactical"]
DEFAULT_MAX_WORKERS = 3
ARCHIVE_LATENCY = 1.0  # stands in for a real archive call over the network

QUESTION = "Should the Pathfinder commit to the Vega Station rescue, and in what order?"

# Logistics and tactical disagree about how long the window stays open. That is
# deliberate — reconcile() has to notice.
ARCHIVES: dict[str, str] = {
    "medical": (
        "MED-301: 14 survivors reported, 3 critical; critical cases need treatment "
        "within 6 hours.\n"
        "MED-305: Sickbay takes 8 at a time; triage doubles throughput with crew support.\n"
        "MED-309: Station radiation is at the edge of tolerance for unshielded EVA."
    ),
    "logistics": (
        "LOG-077: Vega Station docking clamps are rated for our mass; approach takes "
        "2 hours.\n"
        "LOG-081: Station power reserves hold the docking ring stable for about 8 more "
        "hours.\n"
        "LOG-084: Two shuttle round trips are needed to lift 14 survivors."
    ),
    "tactical": (
        "TAC-012: A debris field is drifting across the docking ring; projected to block "
        "approach in about 3 hours.\n"
        "TAC-015: No hostile contacts within sensor range.\n"
        "TAC-019: Shields can clear light debris at reduced speed, adding 40 minutes."
    ),
}

FIXED_BRIEFS: list[tuple[str, str]] = [
    ("medical", "How many survivors need treatment, how urgently, and what can sickbay take?"),
    ("logistics", "How long does the approach take and how long does the docking ring hold?"),
    ("tactical", "What is in the approach path, and when does it stop being flyable?"),
]


# --- The data that crosses the parent/child boundary -------------------------


@dataclass
class Brief:
    """One unit of delegated work. The subagent sees nothing else."""

    department: str
    task: str


class SubagentReport(BaseModel):
    """What a subagent is allowed to hand back. Everything else stays in its context."""

    claim: str = Field(description="One sentence the lead agent can act on.")
    evidence: list[str] = Field(description="Archive record IDs you relied on.")
    window_hours: float | None = Field(
        description=(
            "Hours until the rescue window closes, if your archive says so. "
            "Null if your records do not cover it."
        )
    )
    confidence: float = Field(description="0-1 confidence in the claim.")


@dataclass
class Finding:
    """A report plus the provenance the parent attaches - never the child."""

    brief: Brief
    report: SubagentReport
    raw_chars: int = 0  # how much the subagent read to produce this

    @property
    def department(self) -> str:
        return self.brief.department


@dataclass
class Reconciled:
    """The deterministic pass over the findings, before any model sees them."""

    findings: list[Finding] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)


# --- Subagent tool ----------------------------------------------------------


async def read_archive(department: str, query: str) -> str:
    """Mock archive read, scoped to one department. Sleeps like a real call."""
    await asyncio.sleep(ARCHIVE_LATENCY)
    lines = ARCHIVES.get(department, "").splitlines()
    words = [w for w in query.lower().split() if len(w) > 3]
    hits = [line for line in lines if any(w in line.lower() for w in words)]
    return "\n".join(hits or lines)


ARCHIVE_TOOL = {
    "type": "function",
    "name": "read_archive",
    "description": "Read your own department's archive for records on a topic.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Topic to look up, e.g. docking ring"}
        },
        "required": ["query"],
    },
}


# --- Lead agent tool --------------------------------------------------------

SPAWN_TOOL = {
    "type": "function",
    "name": "spawn_researchers",
    "description": (
        "Spawn subagents to research independent sub-questions, each in its own "
        "context window. Pass every brief in one call — they all run at the same "
        "time. Maximum three."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "briefs": {
                "type": "array",
                "description": "One entry per independent sub-question.",
                "items": {
                    "type": "object",
                    "properties": {
                        "department": {
                            "type": "string",
                            "enum": DEPARTMENTS,
                            "description": "Which archive this subagent is allowed to read.",
                        },
                        "task": {
                            "type": "string",
                            "description": (
                                "A self-contained brief. The subagent cannot see this "
                                "conversation, so repeat anything it needs to know."
                            ),
                        },
                    },
                    "required": ["department", "task"],
                },
            }
        },
        "required": ["briefs"],
    },
}


# --- Prompts ----------------------------------------------------------------

SUBAGENT_PROMPTS: dict[str, str] = {
    "medical": (
        "You are the Chief Medical Officer aboard the DSS Pathfinder, working as a "
        "subagent. You have exactly one job, given below. Call read_archive to gather "
        "evidence, then file your report. Your report is the only thing the lead agent "
        "will ever see, so make the claim stand on its own. Ignore anything outside "
        "your job — another subagent has it."
    ),
    "logistics": (
        "You are the Logistics Officer aboard the DSS Pathfinder, working as a "
        "subagent. You have exactly one job, given below. Call read_archive to gather "
        "evidence, then file your report. Your report is the only thing the lead agent "
        "will ever see, so make the claim stand on its own. Ignore anything outside "
        "your job — another subagent has it."
    ),
    "tactical": (
        "You are the Tactical Officer aboard the DSS Pathfinder, working as a "
        "subagent. You have exactly one job, given below. Call read_archive to gather "
        "evidence, then file your report. Your report is the only thing the lead agent "
        "will ever see, so make the claim stand on its own. Ignore anything outside "
        "your job — another subagent has it."
    ),
}

LEAD_PROMPT = (
    "You are the lead agent on the bridge of the DSS Pathfinder. You have no archive "
    "access of your own — spawn researchers instead.\n"
    "Split the question into independent briefs and pass them all in a single "
    "spawn_researchers call so they run concurrently. Do not spawn one, read it, and "
    "then spawn the next.\n"
    "Once the reports are back, answer in three or four sentences and say plainly if "
    "they disagree. Do not spawn a second round."
)

MERGER_PROMPT = (
    "You are the lead agent merging subagent reports into one answer for the Captain. "
    "Never average conflicting numbers — name the disagreement, say which source you "
    "trust and why, and recommend an action. Four sentences maximum."
)
