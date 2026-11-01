"""
Exercise 01 — Structured Tracing

Give every request a trace ID and every unit of work inside it a span, so a
single request can be reconstructed afterwards from the logs alone.

No API key: the pipeline in __main__ simulates work with short sleeps. The
clock is injectable, so the tests drive durations instead of waiting for them.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Callable

logger = logging.getLogger("pathfinder.trace")


def log_json(record: dict) -> None:
    """Default span emitter — one JSON object per line."""
    logger.info(json.dumps(record))


class TraceContext:
    """
    Collects the spans for one request.

    A span is one unit of work: a retrieval, an LLM call, a guardrail check.
    Spans opened while another span is open become its children, so the
    completed list forms a tree.

    Args:
        trace_id: Reuse an inbound ID (from a header, say) or let it generate one.
        clock: Returns seconds as a float. Monotonic by default so that a
            system clock adjustment mid-request cannot produce a negative
            duration. The tests pass a fake.
        emit: Called with each completed span dict. Defaults to a JSON log line.
    """

    def __init__(
        self,
        trace_id: str | None = None,
        clock: Callable[[], float] = time.monotonic,
        emit: Callable[[dict], None] = log_json,
    ):
        self.trace_id = trace_id or uuid.uuid4().hex[:16]
        self.spans: list[dict] = []  # completed spans, in completion order
        self._open: dict[str, dict] = {}
        self._stack: list[str] = []  # currently open span IDs, innermost last
        self._seq = 0  # start order, so summary() can sort siblings
        self._clock = clock
        self._emit = emit

    def start_span(self, name: str, metadata: dict | None = None) -> str:
        """
        Open a span and return its ID.

        The span dict you store needs at least:

            {
                "span_id": str,          # uuid4().hex[:12]
                "trace_id": self.trace_id,
                "parent_id": str | None, # the span that is currently open
                "name": name,
                "seq": int,              # self._seq, then increment it
                "start": self._clock(),
                "metadata": dict,
            }

        TODO:
        - Generate a span_id.
        - parent_id is the innermost open span (end of self._stack), or None.
        - Build the span dict, store it in self._open, push the ID onto self._stack.
        - Return the span_id.
        """
        # TODO: open a span
        pass

    def end_span(
        self,
        span_id: str,
        metadata: dict | None = None,
        status: str = "ok",
    ) -> dict:
        """
        Close a span, record how long it took, and emit it.

        Returns the completed span, which now also carries:

            {"duration_ms": float, "status": status}

        TODO:
        - Pop the span out of self._open and remove its ID from self._stack.
        - duration_ms = (self._clock() - span["start"]) * 1000, rounded to 1dp.
        - Set status, merge in metadata (update, do not replace).
        - Append to self.spans.
        - Call self._emit with a flat dict: trace_id, span_id, parent_id, name,
          duration_ms, status, and the metadata keys spread in at the top level.
        - Return the span.
        """
        # TODO: close the span and emit it
        pass

    def summary(self) -> str:
        """
        Render the completed spans as an indented tree.

            trace 4f2a9c1e8b3d7a60
              handle_request  142.0ms  [ok]
                retrieve_logs  38.0ms  [ok]
                  embed_query  12.0ms  [ok]
                llm_call  95.0ms  [ok]

        Children indent one level past their parent. Siblings appear in the
        order they were started, which is what "seq" is for — note that
        self.spans is in *completion* order, so an inner span lands in the
        list before the outer span that contains it.

        TODO:
        - First line: f"trace {self.trace_id}".
        - Index the spans by span_id so you can walk parent_id upwards.
        - For each span sorted by "seq": depth = how many parents it has.
        - Append f"{'  ' * (depth + 1)}{name}  {duration_ms}ms  [{status}]".
        - Join with newlines.
        """
        # TODO: render the span tree
        pass


# ---------------------------------------------------------------------------
# A request pipeline to trace — provided. Focus on TraceContext above.
# ---------------------------------------------------------------------------


def handle_query(question: str, trace: TraceContext) -> str:
    """Simulate the Pathfinder answering a crew question, tracing each step."""
    root = trace.start_span("handle_request", {"question": question})

    retrieve = trace.start_span("retrieve_logs")
    embed = trace.start_span("embed_query", {"model": "text-embedding-3-small"})
    time.sleep(0.01)
    trace.end_span(embed, {"dimensions": 1536})
    search = trace.start_span("search_index", {"collection": "ship_logs"})
    time.sleep(0.02)
    trace.end_span(search, {"hits": 3})
    trace.end_span(retrieve, {"passages": 3})

    call = trace.start_span("llm_call", {"model": "gpt-6-luna"})
    time.sleep(0.03)
    answer = "Warp core efficiency has held at 94% since the ion storm."
    trace.end_span(call, {"tokens": 210})

    guard = trace.start_span("guardrail_check")
    time.sleep(0.01)
    trace.end_span(guard, {"passed": True})

    trace.end_span(root, {"status_code": 200})
    return answer


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    trace = TraceContext()
    print(f"Tracing one request — trace_id {trace.trace_id}\n")

    answer = handle_query("How is the warp core holding up?", trace)

    print(f"\nAnswer: {answer}\n")
    summary = trace.summary()
    print(summary if summary else "summary() not implemented yet")
