"""
Exercise 05 — Spawned Subagents (solution)

A lead agent spawns subagents on demand, runs them at once, and reconciles
their reports before answering.

Run:  python solution.py
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import time

from dotenv import load_dotenv
from openai import AsyncOpenAI
from tools import (
    ARCHIVE_TOOL,
    DEFAULT_MAX_WORKERS,
    DEPARTMENTS,
    FIXED_BRIEFS,
    LEAD_PROMPT,
    MERGER_PROMPT,
    QUESTION,
    SPAWN_TOOL,
    SUBAGENT_PROMPTS,
    Brief,
    Finding,
    Reconciled,
    SubagentReport,
    read_archive,
)

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


def build_task_brief(department: str, task: str) -> list[dict]:
    """Opening messages for one subagent: its role, and its one job."""
    prompt = SUBAGENT_PROMPTS.get(department, SUBAGENT_PROMPTS["medical"])
    return [
        {"role": "system", "content": prompt},
        {"role": "user", "content": task},
    ]


def _stub_report(claim: str) -> SubagentReport:
    return SubagentReport(claim=claim, evidence=[], window_hours=None, confidence=0.0)


async def run_subagent(brief: Brief, client: AsyncOpenAI, max_turns: int = 3) -> Finding:
    """One subagent: fresh context, one scoped tool, a structured report out."""
    messages = build_task_brief(brief.department, brief.task)
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
            return Finding(brief=brief, report=report, raw_chars=raw_chars)

        messages += response.output
        for call in calls:
            try:
                args = json.loads(call.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            observation = await read_archive(brief.department, args.get("query", ""))
            raw_chars += len(observation)
            messages.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": observation,
                }
            )

    return Finding(
        brief=brief,
        report=_stub_report("Ran out of turns before reporting."),
        raw_chars=raw_chars,
    )


async def run_serial(briefs: list[Brief], client: AsyncOpenAI) -> list[Finding]:
    """One subagent after another — the baseline fan_out has to beat."""
    return [await run_subagent(brief, client) for brief in briefs]


async def fan_out(
    briefs: list[Brief], client: AsyncOpenAI, max_workers: int = DEFAULT_MAX_WORKERS
) -> list[Finding]:
    """Every brief at once, capped at max_workers, one failure left standing.

    The result lines up index-for-index with `briefs`, so a caller matching
    findings back to tool calls never has to guess which one dropped out.
    """
    limit = asyncio.Semaphore(max_workers)

    async def guarded(brief: Brief) -> Finding:
        async with limit:
            return await run_subagent(brief, client)

    settled = await asyncio.gather(
        *(guarded(brief) for brief in briefs), return_exceptions=True
    )

    findings: list[Finding] = []
    for brief, outcome in zip(briefs, settled, strict=True):
        if isinstance(outcome, BaseException):
            findings.append(Finding(brief=brief, report=_stub_report(f"Failed: {outcome}")))
        else:
            findings.append(outcome)
    return findings


def _to_brief(item: dict) -> Brief:
    """One brief the model wrote. It picked the department, so check it."""
    department = item.get("department", "")
    return Brief(
        department=department if department in DEPARTMENTS else DEPARTMENTS[0],
        task=item.get("task", ""),
    )


def spawn_calls(response) -> list:
    """The spawn_researchers calls in a lead turn (empty if the lead answered)."""
    return [
        item
        for item in response.output
        if item.type == "function_call" and item.name == "spawn_researchers"
    ]


async def handle_spawn_calls(
    response, client: AsyncOpenAI, max_workers: int = DEFAULT_MAX_WORKERS
) -> tuple[list, list[Finding]]:
    """Run every subagent the lead asked for in this turn, concurrently.

    One call carries a list of briefs, and a turn can carry more than one call,
    so flatten the lot into a single fan-out and slice the reports back per call.

    Returns:
        (new_items, findings) — new_items is one function_call_output per call,
        ready to extend the lead's conversation.
    """
    calls = spawn_calls(response)
    if not calls:
        return [], []

    groups: list[list[Brief]] = []
    for call in calls:
        try:
            args = json.loads(call.arguments or "{}")
        except json.JSONDecodeError:
            args = {}
        groups.append([_to_brief(item) for item in args.get("briefs", [])])

    briefs = [brief for group in groups for brief in group]
    findings = await fan_out(briefs, client, max_workers=max_workers)

    new_items = []
    cursor = 0
    for call, group in zip(calls, groups, strict=True):
        chunk = findings[cursor : cursor + len(group)]
        cursor += len(group)
        new_items.append(
            {
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": json.dumps([finding.report.model_dump() for finding in chunk]),
            }
        )
    return new_items, findings


def _normalise(claim: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", claim.lower()).strip()


def reconcile(findings: list[Finding]) -> Reconciled:
    """Deterministic pass over the reports, before any model sees them.

    Only the fields you asked for as data are checkable here. The prose claim
    is not — which is why window_hours is a number, not a sentence.
    """
    kept: list[Finding] = []
    duplicates: list[str] = []
    seen: dict[str, str] = {}

    for finding in findings:
        key = _normalise(finding.report.claim)
        if key and key in seen:
            duplicates.append(
                f"{finding.department} repeats {seen[key]}: {finding.report.claim}"
            )
            continue
        if key:
            seen[key] = finding.department
        kept.append(finding)

    conflicts: list[str] = []
    windows = {
        finding.department: finding.report.window_hours
        for finding in kept
        if finding.report.window_hours is not None
    }
    if len(windows) >= 2:
        spread = max(windows.values()) - min(windows.values())
        if spread >= 2:
            detail = ", ".join(f"{dept} {hours:g}h" for dept, hours in windows.items())
            conflicts.append(f"window closes {spread:g}h apart ({detail})")

    unsure = [f.department for f in kept if f.report.confidence < 0.5]
    if unsure:
        conflicts.append(f"low confidence from {', '.join(unsure)}")

    return Reconciled(findings=kept, conflicts=conflicts, duplicates=duplicates)


async def synthesise(question: str, reconciled: Reconciled, client: AsyncOpenAI) -> str:
    """One merge call: the reports plus the conflicts code already found."""
    briefing = "\n".join(
        f"[{finding.department}] {finding.report.claim} "
        f"(window={finding.report.window_hours}, "
        f"confidence={finding.report.confidence:.2f}, "
        f"evidence={', '.join(finding.report.evidence) or 'none cited'})"
        for finding in reconciled.findings
    )
    flagged = "\n".join(f"- {c}" for c in reconciled.conflicts) or "- none"

    response = await client.responses.create(
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


async def lead_loop(
    question: str,
    client: AsyncOpenAI,
    max_workers: int = DEFAULT_MAX_WORKERS,
    max_turns: int = 3,
) -> dict:
    """The lead decides the fan-out, then the findings are reconciled and merged.

    Returns:
        {"answer": str, "findings": list[Finding], "conflicts": list[str],
         "duplicates": list[str], "trace": list[dict]}
    """
    messages: list = [
        {"role": "system", "content": LEAD_PROMPT},
        {"role": "user", "content": question},
    ]
    findings: list[Finding] = []
    trace: list[dict] = []

    for turn in range(1, max_turns + 1):
        response = await client.responses.create(
            model=MODEL,
            reasoning={"effort": "none"},
            input=messages,
            tools=[SPAWN_TOOL],
            tool_choice="auto",
            parallel_tool_calls=True,  # let it ask for several children at once
        )
        calls = spawn_calls(response)

        if not calls:
            trace.append({"turn": turn, "action": "lead_draft", "text": response.output_text})
            if not findings:
                # The lead answered without delegating anything.
                return {
                    "answer": response.output_text,
                    "findings": [],
                    "conflicts": [],
                    "duplicates": [],
                    "trace": trace,
                }
            break

        messages += response.output
        new_items, spawned = await handle_spawn_calls(response, client, max_workers=max_workers)
        messages.extend(new_items)
        findings.extend(spawned)
        for finding in spawned:
            trace.append(
                {
                    "turn": turn,
                    "action": "subagent",
                    "department": finding.department,
                    "task": finding.brief.task,
                    "claim": finding.report.claim,
                }
            )

    reconciled = reconcile(findings)
    trace.append(
        {
            "turn": "merge",
            "action": "reconcile",
            "conflicts": len(reconciled.conflicts),
            "duplicates": len(reconciled.duplicates),
        }
    )
    answer = await synthesise(question, reconciled, client)
    return {
        "answer": answer,
        "findings": reconciled.findings,
        "conflicts": reconciled.conflicts,
        "duplicates": reconciled.duplicates,
        "trace": trace,
    }


async def run_fixed_briefs(
    question: str,
    client: AsyncOpenAI,
    max_workers: int = DEFAULT_MAX_WORKERS,
    concurrent: bool = True,
) -> dict:
    """The same pipeline with briefs written by hand instead of by the model."""
    briefs = [Brief(dept, task) for dept, task in FIXED_BRIEFS]
    findings = (
        await fan_out(briefs, client, max_workers=max_workers)
        if concurrent
        else await run_serial(briefs, client)
    )
    reconciled = reconcile(findings)
    answer = await synthesise(question, reconciled, client)
    return {
        "answer": answer,
        "findings": reconciled.findings,
        "conflicts": reconciled.conflicts,
        "duplicates": reconciled.duplicates,
        "trace": [
            {
                "turn": "fixed",
                "action": "subagent",
                "department": finding.department,
                "claim": finding.report.claim,
            }
            for finding in reconciled.findings
        ],
    }


def print_result(result: dict) -> None:
    for finding in result["findings"]:
        print(f"  [{finding.department}] {finding.report.claim}")
    for conflict in result["conflicts"]:
        print(f"  ! conflict: {conflict}")
    for duplicate in result["duplicates"]:
        print(f"  ~ duplicate: {duplicate}")

    raw = sum(f.raw_chars for f in result["findings"])
    passed_up = sum(len(f.report.model_dump_json()) for f in result["findings"])
    if raw:
        print(f"  Subagents read {raw} chars; the lead received {passed_up}.")
    print(f"Lead: {result['answer']}\n")


def main():
    client = AsyncOpenAI()
    max_workers = DEFAULT_MAX_WORKERS
    mode = "spawn"
    last_result = None

    print("=" * 60)
    print("  MODULE 9 — Spawned Subagents")
    print("  DSS Pathfinder Multi-Agent System")
    print("=" * 60)
    print("Commands: /mode spawn|fixed|serial, /workers N, /trace, /archives, quit")
    print(f"Try: {QUESTION}\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input == "/archives":
            print("[Department archives]")
            for dept in DEPARTMENTS:
                print(f"  {dept}")
            print()
            continue

        if user_input.startswith("/mode "):
            choice = user_input[6:].strip().lower()
            if choice in ("spawn", "fixed", "serial"):
                mode = choice
                print(f"[Mode set to: {mode}]\n")
            else:
                print("[Valid: spawn, fixed, serial]\n")
            continue

        if user_input.startswith("/workers "):
            parts = user_input.split()
            if len(parts) == 2 and parts[1].isdigit() and int(parts[1]) > 0:
                max_workers = int(parts[1])
                print(f"[Max workers set to {max_workers}]\n")
            else:
                print("[Usage: /workers N]\n")
            continue

        if user_input == "/trace":
            if last_result is None:
                print("[No trace yet — ask a question first]\n")
            else:
                print("[Subagent trace]")
                for step in last_result["trace"]:
                    print(f"  {step}")
                print()
            continue

        print(f"[Running: {mode}, up to {max_workers} workers...]")
        start = time.perf_counter()
        if mode == "spawn":
            last_result = asyncio.run(lead_loop(user_input, client, max_workers=max_workers))
        else:
            last_result = asyncio.run(
                run_fixed_briefs(
                    user_input, client, max_workers=max_workers, concurrent=mode == "fixed"
                )
            )
        print(f"[{time.perf_counter() - start:.1f}s]")
        print_result(last_result)


if __name__ == "__main__":
    main()
