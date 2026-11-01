"""
Exercise 01 — Structured Tracing (solution)

Give every request a trace ID and every unit of work inside it a span, so a
single request can be reconstructed afterwards from the logs alone.
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
    """Collects the spans for one request."""

    def __init__(
        self,
        trace_id: str | None = None,
        clock: Callable[[], float] = time.monotonic,
        emit: Callable[[dict], None] = log_json,
    ):
        self.trace_id = trace_id or uuid.uuid4().hex[:16]
        self.spans: list[dict] = []
        self._open: dict[str, dict] = {}
        self._stack: list[str] = []
        self._seq = 0
        self._clock = clock
        self._emit = emit

    def start_span(self, name: str, metadata: dict | None = None) -> str:
        span_id = uuid.uuid4().hex[:12]
        span = {
            "span_id": span_id,
            "trace_id": self.trace_id,
            "parent_id": self._stack[-1] if self._stack else None,
            "name": name,
            "seq": self._seq,
            "start": self._clock(),
            "metadata": dict(metadata or {}),
        }
        self._seq += 1
        self._open[span_id] = span
        self._stack.append(span_id)
        return span_id

    def end_span(
        self,
        span_id: str,
        metadata: dict | None = None,
        status: str = "ok",
    ) -> dict:
        span = self._open.pop(span_id)
        if span_id in self._stack:
            self._stack.remove(span_id)

        span["duration_ms"] = round((self._clock() - span["start"]) * 1000, 1)
        span["status"] = status
        if metadata:
            span["metadata"].update(metadata)
        self.spans.append(span)

        self._emit(
            {
                "trace_id": span["trace_id"],
                "span_id": span["span_id"],
                "parent_id": span["parent_id"],
                "name": span["name"],
                "duration_ms": span["duration_ms"],
                "status": span["status"],
                **span["metadata"],
            }
        )
        return span

    def summary(self) -> str:
        lines = [f"trace {self.trace_id}"]
        by_id = {span["span_id"]: span for span in self.spans}

        for span in sorted(self.spans, key=lambda s: s["seq"]):
            depth = 0
            parent_id = span["parent_id"]
            while parent_id is not None and parent_id in by_id:
                depth += 1
                parent_id = by_id[parent_id]["parent_id"]
            indent = "  " * (depth + 1)
            lines.append(
                f"{indent}{span['name']}  {span['duration_ms']}ms  [{span['status']}]"
            )

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# A request pipeline to trace — provided.
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
    print(trace.summary())
