"""Part 6: A lead agent spawns subagents, runs them at once, then reconciles.

Parts 1-5 all share one roster of agents fixed in the source. Here the lead
creates workers on demand, each in its own context window, and only ever sees
what they report back.

Run alone:  python module-09-multi-agent/demo/06_subagents.py
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
TOOL_LATENCY = 1.0  # stands in for a real archive call over the network
MAX_WORKERS = 3

QUESTION = "Can the DSS Pathfinder transit the Kepler-9 corridor in the next 12 hours?"

# Navigation and science disagree about the storm. That is deliberate — it is
# what Part C has to notice.
ARCHIVES = {
    "navigation": (
        "NAV-114: Kepler-9 corridor is clear of debris; two freighters inbound.\n"
        "NAV-118: Long-range plot puts the ion storm front at the corridor mouth "
        "in about 9 hours.\n"
        "NAV-121: Transit at full burn takes 5 hours."
    ),
    "engineering": (
        "ENG-402: Reactor nominal at 94%; +18% sustained available for 6 hours.\n"
        "ENG-407: Shield emitters re-tuned two days ago, rated for moderate ion flux.\n"
        "ENG-411: Port coolant loop runs four degrees warm above 90% output."
    ),
    "science": (
        "SCI-233: Ion storm is accelerating; the latest sweep puts the front at the "
        "corridor mouth in roughly 4 hours.\n"
        "SCI-236: Flux density at the front measures three times the emitter rating.\n"
        "SCI-240: Storm interior blinds long-range sensors."
    ),
}

BRIEFS_BY_HAND = [
    ("navigation", "How long is the transit, and what is in the corridor right now?"),
    ("engineering", "Can the shields and reactor take a run through ion flux?"),
    ("science", "When does the ion storm reach the corridor, and how severe is it?"),
]


# ---------------------------------------------------------------------------
# The subagent's one tool
# ---------------------------------------------------------------------------

ARCHIVE_TOOL = {
    "type": "function",
    "name": "read_archive",
    "description": "Read your own department's survey archive for records on a topic.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Topic to look up, e.g. ion storm"}
        },
        "required": ["query"],
    },
}


async def read_archive(department: str, query: str) -> str:
    """Mock archive read, scoped to one department."""
    await asyncio.sleep(TOOL_LATENCY)
    lines = ARCHIVES.get(department, "").splitlines()
    words = [w for w in query.lower().split() if len(w) > 3]
    hits = [line for line in lines if any(w in line.lower() for w in words)]
    return "\n".join(hits or lines)


# ---------------------------------------------------------------------------
# One subagent
# ---------------------------------------------------------------------------


class SubagentReport(BaseModel):
    headline: str = Field(description="One sentence the lead agent can act on.")
    evidence: list[str] = Field(description="Archive record IDs you relied on.")
    storm_eta_hours: float | None = Field(
        description=(
            "Hours until the ion storm reaches the corridor, if your archive says. "
            "Null if your records do not cover it."
        )
    )
    confidence: float = Field(description="0-1 confidence in the headline.")


@dataclass
class Brief:
    department: str
    task: str


@dataclass
class Result:
    brief: Brief
    report: SubagentReport
    raw_chars: int  # everything the subagent itself read


SUBAGENT_PROMPT = (
    "You are the {department} specialist aboard the DSS Pathfinder, working as a "
    "subagent. You have exactly one job, given below. Call read_archive to gather "
    "evidence, then file your report. Your report is the only thing the lead agent "
    "will ever see, so make the headline stand on its own. Ignore anything outside "
    "your job — another subagent has it."
)


def _stub_report(headline: str) -> SubagentReport:
    return SubagentReport(headline=headline, evidence=[], storm_eta_hours=None, confidence=0.0)


async def run_subagent(brief: Brief, client: AsyncOpenAI, max_turns: int = 3) -> Result:
    """One subagent: fresh context, scoped tool, structured report out."""
    messages: list = [
        {"role": "system", "content": SUBAGENT_PROMPT.format(department=brief.department)},
        {"role": "user", "content": brief.task},
    ]
    raw_chars = sum(len(m["content"]) for m in messages)

    for _ in range(max_turns):
        response = await client.responses.parse(
            model=MODEL,
            reasoning={"effort": "none"},
            input=messages,
            tools=[ARCHIVE_TOOL],
            tool_choice="auto",
            text_format=SubagentReport,
        )
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            report = response.output_parsed or _stub_report("Filed nothing usable.")
            return Result(brief, report, raw_chars)

        messages += response.output
        for call in calls:
            args = json.loads(call.arguments or "{}")
            observation = await read_archive(brief.department, args.get("query", ""))
            raw_chars += len(observation)
            messages.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": observation,
                }
            )

    return Result(brief, _stub_report("Ran out of turns before reporting."), raw_chars)


# ---------------------------------------------------------------------------
# Fan-out and fan-in
# ---------------------------------------------------------------------------


async def run_serial(briefs: list[Brief], client: AsyncOpenAI) -> list[Result]:
    return [await run_subagent(brief, client) for brief in briefs]


async def fan_out(
    briefs: list[Brief], client: AsyncOpenAI, max_workers: int = MAX_WORKERS
) -> list[Result]:
    """Every brief at once, capped at max_workers. One failure does not sink the rest.

    The returned list lines up with `briefs`, so a caller matching results back to
    tool calls does not have to guess which one dropped out.
    """
    limit = asyncio.Semaphore(max_workers)

    async def guarded(brief: Brief) -> Result:
        async with limit:
            return await run_subagent(brief, client)

    settled = await asyncio.gather(
        *(guarded(brief) for brief in briefs), return_exceptions=True
    )

    results: list[Result] = []
    for brief, outcome in zip(briefs, settled, strict=True):
        if isinstance(outcome, BaseException):
            print(f"    ! {brief.department} subagent failed: {outcome}")
            results.append(Result(brief, _stub_report(f"Failed: {outcome}"), 0))
        else:
            results.append(outcome)
    return results


def reconcile(results: list[Result]) -> list[str]:
    """Deterministic pass over the reports, before any model sees them.

    You can only check in code what you asked the subagents for as data — the
    numeric ETA field is checkable, the prose headline is not.
    """
    conflicts: list[str] = []

    etas = {
        result.brief.department: result.report.storm_eta_hours
        for result in results
        if result.report.storm_eta_hours is not None
    }
    if len(etas) >= 2:
        spread = max(etas.values()) - min(etas.values())
        if spread >= 2:
            detail = ", ".join(f"{dept} {hours:g}h" for dept, hours in etas.items())
            conflicts.append(f"storm ETA disagrees by {spread:g}h ({detail})")

    unsure = [r.brief.department for r in results if r.report.confidence < 0.5]
    if unsure:
        conflicts.append(f"low confidence from {', '.join(unsure)}")

    return conflicts


MERGER_PROMPT = (
    "You are the lead agent merging subagent reports into one answer for the Captain. "
    "Never average conflicting numbers — name the disagreement, say which source you "
    "trust and why, and recommend an action. Four sentences maximum."
)


def synthesise(question: str, results: list[Result], conflicts: list[str], client: OpenAI) -> str:
    briefing = "\n".join(
        f"[{r.brief.department}] {r.report.headline} "
        f"(eta={r.report.storm_eta_hours}, confidence={r.report.confidence:.2f}, "
        f"evidence={', '.join(r.report.evidence) or 'none cited'})"
        for r in results
    )
    flagged = "\n".join(f"- {c}" for c in conflicts) or "- none"
    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=[
            {"role": "system", "content": MERGER_PROMPT},
            {
                "role": "user",
                "content": (
                    f"QUESTION: {question}\n\nREPORTS:\n{briefing}\n\n"
                    f"CONFLICTS ALREADY FLAGGED IN CODE:\n{flagged}"
                ),
            },
        ],
    )
    return response.output_text


# ---------------------------------------------------------------------------
# The lead agent decides the fan-out itself
# ---------------------------------------------------------------------------

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
                            "enum": ["navigation", "engineering", "science"],
                            "description": "Which archive this subagent gets to read.",
                        },
                        "task": {
                            "type": "string",
                            "description": (
                                "A self-contained brief. The subagent cannot see this "
                                "conversation, so repeat anything it needs."
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

LEAD_PROMPT = (
    "You are the lead agent on the bridge of the DSS Pathfinder. You have no archive "
    "access of your own — spawn researchers instead.\n"
    "Split the question into independent briefs and pass them all in a single "
    "spawn_researchers call so they run concurrently. Do not spawn one, read it, and "
    "then spawn the next.\n"
    "Once the reports are back, answer in three or four sentences and say plainly if "
    "they disagree. Do not spawn a second round."
)


async def lead_with_spawn_tool(
    question: str, client: AsyncOpenAI, max_turns: int = 5
) -> tuple[str, list[Result]]:
    messages: list = [
        {"role": "system", "content": LEAD_PROMPT},
        {"role": "user", "content": question},
    ]
    spawned: list[Result] = []

    for turn in range(1, max_turns + 1):
        response = await client.responses.create(
            model=MODEL,
            reasoning={"effort": "none"},
            input=messages,
            tools=[SPAWN_TOOL],
            tool_choice="auto",
            parallel_tool_calls=True,  # let it ask for several children at once
        )
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            return response.output_text, spawned

        messages += response.output

        # A call carries a list of briefs; a turn can carry several calls. Flatten
        # the lot into one fan-out, then slice the reports back per call_id.
        groups: list[list[Brief]] = []
        for call in calls:
            args = json.loads(call.arguments or "{}")
            groups.append(
                [
                    Brief(item.get("department", "science"), item.get("task", question))
                    for item in args.get("briefs", [])
                ]
            )

        briefs = [brief for group in groups for brief in group]
        plural = "s" if len(briefs) != 1 else ""
        print(f"  Turn {turn}: the lead spawned {len(briefs)} researcher{plural} at once:")
        for brief in briefs:
            print(f"    {brief.department:>12}: {brief.task}")
        print()

        results = await fan_out(briefs, client)
        spawned.extend(results)

        cursor = 0
        for call, group in zip(calls, groups, strict=True):
            chunk = results[cursor : cursor + len(group)]
            cursor += len(group)
            messages.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps([r.report.model_dump() for r in chunk]),
                }
            )

    return f"(still spawning after {max_turns} turns — cut off)", spawned


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------


def print_reports(results: list[Result]) -> None:
    for result in results:
        eta = (
            f"{result.report.storm_eta_hours:g}h"
            if result.report.storm_eta_hours is not None
            else "-"
        )
        print(f"    {result.brief.department:>12}: {result.report.headline}")
        print(f"                  eta {eta}, confidence {result.report.confidence:.2f}")
    print()


async def _run(client: OpenAI):
    async_client = AsyncOpenAI()
    briefs = [Brief(dept, task) for dept, task in BRIEFS_BY_HAND]

    print(f"  Question: {QUESTION}\n")

    print("  --- A. Three subagents, serially then all at once ---\n")
    for brief in briefs:
        print(f"    {brief.department:>12}: {brief.task}")
    print()

    start = time.perf_counter()
    await run_serial(briefs, async_client)
    serial_seconds = time.perf_counter() - start
    print(f"    serial:   {serial_seconds:.1f}s")

    start = time.perf_counter()
    results = await fan_out(briefs, async_client)
    parallel_seconds = time.perf_counter() - start
    print(f"    parallel: {parallel_seconds:.1f}s")
    speedup = serial_seconds / parallel_seconds if parallel_seconds else 1.0
    print(f"    {speedup:.1f}x faster, same work, {MAX_WORKERS} workers\n")

    print_reports(results)

    raw = sum(r.raw_chars for r in results)
    summarised = sum(len(r.report.model_dump_json()) for r in results)
    share = 100 * summarised / raw if raw else 0
    print(f"    The subagents read {raw} characters between them.")
    print(f"    The lead received {summarised} — {share:.0f}% of it.")
    print("    That gap, not the stopwatch, is the real reason to spawn.\n")

    print("  --- B. The lead writes the briefs itself (spawn_researchers) ---\n")
    answer, _ = await lead_with_spawn_tool(QUESTION, async_client)
    print(f"  Lead's answer: {answer}\n")
    print("  Nobody wrote that fan-out. The model chose how many to spawn,")
    print("  which archive each one got, and what to ask it.\n")

    print("  --- C. Reconciling the reports from A ---\n")
    conflicts = reconcile(results)
    if conflicts:
        for conflict in conflicts:
            print(f"    conflict: {conflict}")
    else:
        print("    no conflict detectable in code")
    print()
    print(f"  Merged answer: {synthesise(QUESTION, results, conflicts, client)}\n")


def demo_subagents(client: OpenAI):
    print("=" * 60)
    print("PART 6: SPAWNED SUBAGENTS")
    print("=" * 60)
    print()
    print("  A swarm hands control sideways and never gets it back. A spawned")
    print("  subagent is handed work and hands back a result.")
    print(f"  (Each archive read sleeps {TOOL_LATENCY:g}s to stand in for a real call.)")
    print()
    asyncio.run(_run(client))


if __name__ == "__main__":
    demo_subagents(OpenAI())
