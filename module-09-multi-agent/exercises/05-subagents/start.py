"""
Exercise 05 — Spawned Subagents

A lead agent spawns subagents on demand, runs them at once, and reconciles
their reports before answering.

Run:  python start.py
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
    """Opening messages for one subagent: its role, and its one job.

    Steps:
        1. Look up SUBAGENT_PROMPTS[department] (fall back to medical)
        2. Return a system message with that prompt and a user message with the task

    The subagent sees nothing else — no lead conversation, no sibling reports.
    """
    # TODO: implement
    raise NotImplementedError("TODO")


def _stub_report(claim: str) -> SubagentReport:
    """A report for when a subagent produced nothing usable."""
    return SubagentReport(claim=claim, evidence=[], window_hours=None, confidence=0.0)


async def run_subagent(brief: Brief, client: AsyncOpenAI, max_turns: int = 3) -> Finding:
    """One subagent: fresh context, one scoped tool, a structured report out.

    Steps:
        1. messages = build_task_brief(...); track how many characters it reads
           in raw_chars (start with the length of its own messages)
        2. Loop up to max_turns: await client.responses.parse with
           model=MODEL, reasoning={"effort": "none"}, input=messages,
           tools=[ARCHIVE_TOOL], tool_choice="auto", text_format=SubagentReport
        3. No function_call items in response.output means it filed its report —
           return Finding(brief=brief, report=response.output_parsed, raw_chars=raw_chars)
        4. Otherwise extend messages with response.output, then for each call
           await read_archive(brief.department, args["query"]), add its length to
           raw_chars, and append
           {"type": "function_call_output", "call_id": ..., "output": observation}
        5. Out of turns: return a Finding wrapping _stub_report(...)
    """
    # TODO: implement
    raise NotImplementedError("TODO")


async def run_serial(briefs: list[Brief], client: AsyncOpenAI) -> list[Finding]:
    """One subagent after another — the baseline fan_out has to beat."""
    return [await run_subagent(brief, client) for brief in briefs]


async def fan_out(
    briefs: list[Brief], client: AsyncOpenAI, max_workers: int = DEFAULT_MAX_WORKERS
) -> list[Finding]:
    """Every brief at once, capped at max_workers, one failure left standing.

    Steps:
        1. limit = asyncio.Semaphore(max_workers)
        2. Define an inner coroutine that takes the semaphore
           (`async with limit:`) before awaiting run_subagent
        3. settled = await asyncio.gather(*(...), return_exceptions=True)
        4. Walk briefs and settled together. For an exception, append a Finding
           wrapping _stub_report(f"Failed: {outcome}"); otherwise append the result

    Return a list that lines up index-for-index with `briefs`, so the caller
    matching findings back to tool calls never has to guess which one dropped out.
    """
    # TODO: implement
    raise NotImplementedError("TODO")


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

    One call carries a list of briefs, and a turn can carry more than one call.

    Returns:
        (new_items, findings) — new_items is one function_call_output per call,
        ready to extend the lead's conversation.

    Steps:
        1. calls = spawn_calls(response); if empty, return ([], [])
        2. For each call, parse its arguments and build a list of Briefs from
           args["briefs"] with _to_brief. Keep the per-call grouping
        3. Flatten every group into one list and
           findings = await fan_out(briefs, client, max_workers=max_workers) —
           one fan-out for the whole turn, not one per call
        4. Slice the findings back per call, and append one
           {"type": "function_call_output", "call_id": call.call_id,
            "output": json.dumps([...reports...])} for each
    """
    # TODO: implement
    raise NotImplementedError("TODO")


def _normalise(claim: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", claim.lower()).strip()


def reconcile(findings: list[Finding]) -> Reconciled:
    """Deterministic pass over the reports, before any model sees them.

    Steps:
        1. Drop repeats: _normalise each claim, keep the first department to
           make it, record the rest in `duplicates`
        2. Collect the kept window_hours values that are not None. With two or
           more, flag a conflict if max - min >= 2, naming each department and
           its number
        3. Flag any department reporting confidence < 0.5
        4. Return Reconciled(findings=kept, conflicts=..., duplicates=...)

    Only the fields you asked for as data are checkable here. The prose claim
    is not — which is why window_hours is a number, not a sentence.
    """
    # TODO: implement
    raise NotImplementedError("TODO")


async def synthesise(question: str, reconciled: Reconciled, client: AsyncOpenAI) -> str:
    """One merge call: the reports plus the conflicts code already found.

    Steps:
        1. Build one line per finding: department, claim, window_hours,
           confidence, evidence
        2. Build a flagged-conflicts block from reconciled.conflicts ("- none"
           when it is empty)
        3. await client.responses.create with MERGER_PROMPT as the system
           message and QUESTION / REPORTS / CONFLICTS as the user message
        4. Return response.output_text

    Handing the conflicts to the merger is the point — a model asked to merge
    two different numbers without being told they clash will quietly average them.
    """
    # TODO: implement
    raise NotImplementedError("TODO")


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

    Steps:
        1. messages = LEAD_PROMPT as system + question as user; findings = []
        2. Loop up to max_turns: await client.responses.create with
           input=messages, tools=[SPAWN_TOOL], tool_choice="auto",
           parallel_tool_calls=True (so it can ask for several children at once)
        3. No spawn_calls means the lead is done. If it never spawned anything,
           return its own output_text as the answer. Otherwise break out
        4. Otherwise extend messages with response.output, then with the
           new_items from handle_spawn_calls, and collect the findings
        5. After the loop: reconciled = reconcile(findings), then
           answer = await synthesise(question, reconciled, client)
        6. Record each subagent and the merge step in `trace`
    """
    # TODO: implement
    raise NotImplementedError("TODO")


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
