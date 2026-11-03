"""
Exercise 03: Memory MCP Server — server.py
===========================================
Put memory and compaction behind one MCP server, so any agent can use them
without importing your code.

Run standalone:  mcp dev server.py
"""

import json  # noqa: F401 — you need this in get_thread
import sys

from compaction import (  # noqa: F401 — you need all of these
    BUDGET_TOKENS,
    KEEP_RECENT,
    Anchor,
    compact,
    count_tokens,
)
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
#
# Every tool needs a docstring. MCP sends it to the model as the tool
# description, so it is the only thing telling the agent when to call it.


# TODO: remember(patron, text, kind="preference") -> str
#   Store a durable fact. Call store.remember(text, patron=..., kind=...) and
#   return a line confirming what was stored, including the id.


# TODO: recall(patron, query, k=5) -> str
#   Call store.recall(query, patron=..., k=...) and format the results as
#   lines the model can read: kind, text, score, and id. Say so plainly when
#   there are no matches.


# TODO: forget(memory_id) -> str
#   Call store.forget(memory_id) and report whether it found anything.


# TODO: list_memories(patron) -> str
#   Call store.all_active(patron=...) and list every live memory with its id,
#   so the agent has an id to pass to forget.


# ---- Compaction tools: the harness drives these ----


# TODO: append_turn(thread_id, role, text) -> str
#   threads.setdefault(thread_id, []) then append {"role": role, "content": text}.
#   Return the new message count and count_tokens(thread), so the caller can
#   see the thread growing.


# TODO: thread_budget(thread_id, budget_tokens=BUDGET_TOKENS) -> str
#   Report count_tokens for the thread and whether it is over the budget.
#   The word "over" has to appear when it is over: the client greps for it.


# TODO: merge_anchors(thread_id, new_anchors) -> None
#   Not a tool, a helper. Append only the anchors you have not seen before,
#   comparing on (kind, text) with the case and whitespace stripped. Each pass
#   re-reads the previous compaction block, so the same anchor comes back.


# TODO: compact_thread(thread_id, budget_tokens=BUDGET_TOKENS, keep_recent=KEEP_RECENT) -> str
#   1. look the thread up; say so if there is nothing to compact
#   2. call compact(thread, budget_tokens=..., keep_recent=..., client=client,
#      carried=anchors.get(thread_id, []))
#   3. a None report means it already fits — say so and make no changes
#   4. otherwise store the compacted thread, merge_anchors(thread_id,
#      report.anchors), and return the before/after token counts plus the
#      compaction block itself (compacted[0]["content"])
#   Mention it when report.actual_split != report.requested_split: that is the
#   tool-pair guard doing its job, and it is worth seeing.


# TODO: get_thread(thread_id) -> str
#   Return json.dumps of the thread. The client rebuilds the model's context
#   from this after a compaction, which is how the compaction block actually
#   reaches the model.


# TODO: get_anchors(thread_id) -> str
#   List the anchors carried for a thread.


if __name__ == "__main__":
    mcp.run()
