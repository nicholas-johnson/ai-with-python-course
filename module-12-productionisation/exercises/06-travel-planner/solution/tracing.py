"""Structured tracing for request pipelines."""

import time
import uuid


class TraceContext:
    def __init__(self):
        self.trace_id = str(uuid.uuid4())
        self.spans: list[dict] = []

    def start_span(self, name: str) -> dict:
        span = {
            "span_id": str(uuid.uuid4()),
            "trace_id": self.trace_id,
            "name": name,
            "start_time": time.time(),
        }
        self.spans.append(span)
        return span

    def end_span(self, span: dict, status: str = "ok", metadata: dict | None = None):
        span["end_time"] = time.time()
        span["duration_ms"] = round((span["end_time"] - span["start_time"]) * 1000, 1)
        span["status"] = status
        if metadata:
            span["metadata"] = metadata

    def summary(self) -> str:
        lines = [f"Trace {self.trace_id}"]
        for s in self.spans:
            dur = s.get("duration_ms", "?")
            lines.append(f"  [{s['status']}] {s['name']}: {dur}ms")
        return "\n".join(lines)
