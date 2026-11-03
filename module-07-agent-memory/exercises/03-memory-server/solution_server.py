"""
Exercise 03: Memory MCP Server — solution_server.py
====================================================
Memory and compaction behind one MCP server.

Run standalone:  mcp dev solution_server.py
"""

import sys

from compaction import KEEP_RECENT, Anchor, compact, count_tokens
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from memory_store import MemoryStore, build_collection
from openai import OpenAI

load_dotenv()

mcp = MCPServer("Cantina Memory")

print("Cantina Memory: initialising...", file=sys.stderr, flush=True)
client = OpenAI()
store = MemoryStore(client, build_collection())

# Thread state lives on the server, so an agent can restart and pick up where
# it left off. One entry per thread id.
threads: dict[str, list[dict]] = {}
anchors: dict[str, list[Anchor]] = {}

print("Cantina Memory: ready", file=sys.stderr, flush=True)


# ---- Memory tools: the agent decides when to use these ----


@mcp.tool()
def remember(patron: str, text: str, kind: str = "preference") -> str:
    """Store a durable fact about a patron.

    Use kind="preference" for standing choices, "constraint" for things that
    must always be respected, "identity" for who they are, "commitment" for
    open loops such as an unpaid tab.
    """
    memory_id = store.remember(text, patron=patron, kind=kind)
    return f"Remembered for {patron} [{kind}]: {text} (id {memory_id})"


@mcp.tool()
def recall(patron: str, query: str, k: int = 5) -> str:
    """Recall the memories most relevant to a query, ranked by score."""
    results = store.recall(query, patron=patron, k=k)
    if not results:
        return f"No memories for {patron} matching '{query}'."
    lines = [
        f"- [{memory.kind}] {memory.text} (score {memory.score:.2f}, id {memory.memory_id})"
        for memory in results
    ]
    return "\n".join(lines)


@mcp.tool()
def forget(memory_id: str) -> str:
    """Forget one memory by id. A soft delete: it stops being recalled."""
    if store.forget(memory_id):
        return f"Forgotten: {memory_id}"
    return f"No memory with id {memory_id}"


@mcp.tool()
def list_memories(patron: str) -> str:
    """List every live memory held for a patron."""
    rows = store.all_active(patron=patron)
    if not rows:
        return f"No memories stored for {patron}."
    lines = [
        f"- [{row['kind']}] {row['text']} (id {row['memory_id']})" for row in rows
    ]
    return f"{len(rows)} memories for {patron}:\n" + "\n".join(lines)


# ---- Compaction tools: the harness drives these ----


@mcp.tool()
def append_turn(thread_id: str, role: str, text: str) -> str:
    """Record one turn of a conversation against a thread id."""
    thread = threads.setdefault(thread_id, [])
    thread.append({"role": role, "content": text})
    return f"Thread {thread_id}: {len(thread)} messages, {count_tokens(thread)} tokens"


@mcp.tool()
def thread_budget(thread_id: str, budget_tokens: int = 1200) -> str:
    """Report a thread's token count against a budget."""
    thread = threads.get(thread_id, [])
    tokens = count_tokens(thread)
    verdict = "over budget" if tokens > budget_tokens else "within budget"
    return f"Thread {thread_id}: {tokens} tokens in {len(thread)} messages — {verdict}"


@mcp.tool()
def compact_thread(
    thread_id: str, budget_tokens: int = 1200, keep_recent: int = KEEP_RECENT
) -> str:
    """Compact a thread to fit a budget, preserving its anchors."""
    thread = threads.get(thread_id)
    if not thread:
        return f"No thread {thread_id} to compact."

    compacted, report = compact(
        thread,
        budget_tokens=budget_tokens,
        keep_recent=keep_recent,
        client=client,
        carried=anchors.get(thread_id, []),
    )
    if report is None:
        return f"Thread {thread_id} is already within {budget_tokens} tokens — nothing to do."

    threads[thread_id] = compacted
    anchors.setdefault(thread_id, []).extend(report.anchors)
    moved = (
        f" Boundary moved {report.requested_split} -> {report.actual_split} "
        "to keep a tool pair together."
        if report.actual_split != report.requested_split
        else ""
    )
    return (
        f"Compacted {report.messages_compacted} messages, "
        f"{report.tokens_before} -> {report.tokens_after} tokens.{moved}\n"
        f"{compacted[0]['content']}"
    )


@mcp.tool()
def get_anchors(thread_id: str) -> str:
    """List the decisions, open tasks, and constraints preserved for a thread."""
    carried = anchors.get(thread_id, [])
    if not carried:
        return f"No anchors for {thread_id} — nothing has been compacted yet."
    return "\n".join(f"- [{anchor.kind}] {anchor.text}" for anchor in carried)


if __name__ == "__main__":
    mcp.run()
