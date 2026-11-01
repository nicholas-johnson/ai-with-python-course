"""
Demo 01 — Structured Tracing
==============================
Shows how a trace ID and its spans follow one request through a pipeline.

Needs OPENAI_API_KEY.

Run:  python module-12-productionisation/demo/01_tracing.py
"""

import json
import os
import time
import uuid

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

client = OpenAI()

QUESTION = "How is the warp core holding up after the ion storm?"


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


def demo_traced_request():
    """Trace one crew question through classify, answer, and guardrail steps."""
    print("=" * 60)
    print("  DEMO: Structured Tracing")
    print("=" * 60)

    trace = TraceContext()
    print(f"\nTrace ID: {trace.trace_id}\n")

    # Span 1: classify the query
    span = trace.start_span("classify_query")
    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=[
            {
                "role": "system",
                "content": (
                    "Classify this crew query as one of: status_request, command, "
                    "chitchat. Reply with one word."
                ),
            },
            {"role": "user", "content": QUESTION},
        ],
        max_output_tokens=10,
    )
    classification = response.output_text.strip()
    trace.end_span(
        span,
        metadata={
            "classification": classification,
            "tokens": response.usage.total_tokens,
        },
    )
    print(f"  classify_query    {span['duration_ms']}ms  -> {classification}")

    # Span 2: generate the answer
    span = trace.start_span("generate_response")
    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=[
            {
                "role": "system",
                "content": (
                    "You are the DSS Pathfinder ship AI. Answer the crew briefly. "
                    "The warp core is at 94% efficiency and stable since the storm."
                ),
            },
            {"role": "user", "content": QUESTION},
        ],
        max_output_tokens=100,
    )
    answer = response.output_text.strip()
    trace.end_span(span, metadata={"tokens": response.usage.total_tokens})
    print(f"  generate_response {span['duration_ms']}ms")

    # Span 3: guardrail check
    span = trace.start_span("guardrails_check")
    time.sleep(0.01)
    passed = 0 < len(answer) < 5000
    trace.end_span(
        span, status="ok" if passed else "blocked", metadata={"passed": passed}
    )
    print(f"  guardrails_check  {span['duration_ms']}ms  -> {'passed' if passed else 'blocked'}")

    print(f"\n  Answer: {answer}\n")

    print("--- Spans as JSON, one object per span ---")
    for s in trace.spans:
        safe = {k: v for k, v in s.items() if k not in ("start_time", "end_time")}
        print(json.dumps(safe, indent=2))
    print()
    print(trace.summary())
    print("\n  Searching the logs for that trace ID returns these three spans in order.\n")


if __name__ == "__main__":
    demo_traced_request()
