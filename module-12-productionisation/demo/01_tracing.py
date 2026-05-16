"""
Demo 01 — Structured Tracing
==============================
Shows how TraceContext propagates trace IDs through a request pipeline.

Run:  python module-12-productionisation/demo/01_tracing.py
"""

import json
import time
import uuid

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()


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
    """Simulate a traced AI request pipeline."""
    print("=" * 60)
    print("  DEMO: Structured Tracing")
    print("=" * 60)

    trace = TraceContext()
    print(f"\nTrace ID: {trace.trace_id}\n")

    # Span 1: classify the query
    span = trace.start_span("classify_query")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Classify this query as one of: question, command, chitchat. Reply with one word."},
            {"role": "user", "content": "What's the weather like in Paris?"},
        ],
        max_tokens=10,
    )
    classification = response.choices[0].message.content.strip()
    trace.end_span(span, metadata={"classification": classification, "tokens": response.usage.total_tokens})
    print(f"  Classify: {classification} ({span['duration_ms']}ms)")

    # Span 2: generate response
    span = trace.start_span("generate_response")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Answer briefly."},
            {"role": "user", "content": "What's the weather like in Paris?"},
        ],
        max_tokens=100,
    )
    answer = response.choices[0].message.content.strip()
    trace.end_span(span, metadata={"tokens": response.usage.total_tokens})
    print(f"  Generate: {span['duration_ms']}ms")

    # Span 3: guardrails check
    span = trace.start_span("guardrails_check")
    time.sleep(0.01)
    passed = len(answer) > 0 and len(answer) < 5000
    trace.end_span(span, status="ok" if passed else "blocked", metadata={"passed": passed})
    print(f"  Guardrails: {'passed' if passed else 'blocked'} ({span['duration_ms']}ms)")

    print(f"\n  Answer: {answer}\n")

    # Print full trace as JSON
    print("--- Full trace (JSON) ---")
    for s in trace.spans:
        safe = {k: v for k, v in s.items() if k not in ("start_time", "end_time")}
        print(json.dumps(safe, indent=2))
    print()
    print(trace.summary())


if __name__ == "__main__":
    demo_traced_request()
