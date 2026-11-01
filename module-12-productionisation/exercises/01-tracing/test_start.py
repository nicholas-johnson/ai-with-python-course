"""Tests for Exercise 01 — Structured Tracing."""

import json

from start import TraceContext, handle_query


class FakeClock:
    """A clock the test advances by hand, so durations are exact."""

    def __init__(self):
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def tick(self, seconds: float):
        self.now += seconds


def make_trace(trace_id="trace-1"):
    """A TraceContext with a controllable clock and a captured emitter."""
    clock = FakeClock()
    emitted: list[dict] = []
    trace = TraceContext(trace_id=trace_id, clock=clock, emit=emitted.append)
    return trace, clock, emitted


class TestStartSpan:
    def test_returns_an_id_and_tracks_it_as_open(self):
        trace, _, _ = make_trace()
        span_id = trace.start_span("llm_call")
        assert isinstance(span_id, str)
        assert span_id
        assert trace.spans == []  # not completed yet

    def test_sibling_spans_get_distinct_ids(self):
        trace, _, _ = make_trace()
        first = trace.start_span("embed_query")
        trace.end_span(first)
        second = trace.start_span("search_index")
        assert first != second

    def test_nested_span_records_its_parent(self):
        trace, _, _ = make_trace()
        parent = trace.start_span("handle_request")
        child = trace.start_span("llm_call")
        trace.end_span(child)
        trace.end_span(parent)

        by_name = {span["name"]: span for span in trace.spans}
        assert by_name["handle_request"]["parent_id"] is None
        assert by_name["llm_call"]["parent_id"] == parent

    def test_sibling_after_close_is_not_a_child(self):
        trace, _, _ = make_trace()
        root = trace.start_span("handle_request")
        first = trace.start_span("retrieve_logs")
        trace.end_span(first)
        second = trace.start_span("llm_call")
        trace.end_span(second)
        trace.end_span(root)

        by_name = {span["name"]: span for span in trace.spans}
        assert by_name["llm_call"]["parent_id"] == root

    def test_metadata_is_stored(self):
        trace, _, _ = make_trace()
        span_id = trace.start_span("llm_call", {"model": "gpt-6-luna"})
        span = trace.end_span(span_id)
        assert span["metadata"]["model"] == "gpt-6-luna"


class TestEndSpan:
    def test_records_duration_from_the_clock(self):
        trace, clock, _ = make_trace()
        span_id = trace.start_span("llm_call")
        clock.tick(0.25)
        span = trace.end_span(span_id)
        assert span["duration_ms"] == 250.0

    def test_moves_the_span_into_spans(self):
        trace, _, _ = make_trace()
        span_id = trace.start_span("llm_call")
        trace.end_span(span_id)
        assert len(trace.spans) == 1
        assert trace.spans[0]["span_id"] == span_id

    def test_defaults_to_ok_status(self):
        trace, _, _ = make_trace()
        span = trace.end_span(trace.start_span("llm_call"))
        assert span["status"] == "ok"

    def test_status_can_be_overridden(self):
        trace, _, _ = make_trace()
        span = trace.end_span(trace.start_span("guardrail_check"), status="blocked")
        assert span["status"] == "blocked"

    def test_end_metadata_merges_with_start_metadata(self):
        trace, _, _ = make_trace()
        span_id = trace.start_span("llm_call", {"model": "gpt-6-luna"})
        span = trace.end_span(span_id, {"tokens": 210})
        assert span["metadata"] == {"model": "gpt-6-luna", "tokens": 210}

    def test_emits_a_flat_record_per_span(self):
        trace, clock, emitted = make_trace()
        span_id = trace.start_span("llm_call", {"model": "gpt-6-luna"})
        clock.tick(0.1)
        trace.end_span(span_id, {"tokens": 210})

        assert len(emitted) == 1
        record = emitted[0]
        assert record["trace_id"] == "trace-1"
        assert record["name"] == "llm_call"
        assert record["duration_ms"] == 100.0
        assert record["status"] == "ok"
        assert record["model"] == "gpt-6-luna"  # metadata spread, not nested
        assert record["tokens"] == 210

    def test_emitted_record_is_json_serialisable(self):
        trace, _, emitted = make_trace()
        trace.end_span(trace.start_span("llm_call", {"model": "gpt-6-luna"}))
        json.dumps(emitted[0])  # raises if it is not

    def test_every_span_carries_the_same_trace_id(self):
        trace, _, emitted = make_trace()
        root = trace.start_span("handle_request")
        trace.end_span(trace.start_span("llm_call"))
        trace.end_span(root)
        assert [record["trace_id"] for record in emitted] == ["trace-1", "trace-1"]


class TestSummary:
    def test_first_line_names_the_trace(self):
        trace, _, _ = make_trace()
        assert trace.summary().splitlines()[0] == "trace trace-1"

    def test_indents_children_past_parents(self):
        trace, clock, _ = make_trace()
        root = trace.start_span("handle_request")
        child = trace.start_span("retrieve_logs")
        grandchild = trace.start_span("embed_query")
        clock.tick(0.01)
        trace.end_span(grandchild)
        trace.end_span(child)
        trace.end_span(root)

        lines = trace.summary().splitlines()
        indents = {
            line.strip().split("  ")[0]: len(line) - len(line.lstrip())
            for line in lines[1:]
        }
        assert indents["handle_request"] == 2
        assert indents["retrieve_logs"] == 4
        assert indents["embed_query"] == 6

    def test_orders_siblings_by_start_not_completion(self):
        trace, _, _ = make_trace()
        root = trace.start_span("handle_request")
        first = trace.start_span("retrieve_logs")
        trace.end_span(first)
        second = trace.start_span("llm_call")
        trace.end_span(second)
        trace.end_span(root)

        names = [line.strip().split("  ")[0] for line in trace.summary().splitlines()[1:]]
        assert names == ["handle_request", "retrieve_logs", "llm_call"]

    def test_includes_duration_and_status(self):
        trace, clock, _ = make_trace()
        span_id = trace.start_span("llm_call")
        clock.tick(0.095)
        trace.end_span(span_id)

        line = trace.summary().splitlines()[1]
        assert "95.0ms" in line
        assert "[ok]" in line

    def test_empty_trace_is_just_the_header(self):
        trace, _, _ = make_trace()
        assert trace.summary() == "trace trace-1"


class TestHandleQuery:
    def test_traces_the_whole_pipeline(self):
        trace, _, emitted = make_trace()
        answer = handle_query("How is the warp core holding up?", trace)

        assert answer
        names = [span["name"] for span in trace.spans]
        assert set(names) == {
            "handle_request",
            "retrieve_logs",
            "embed_query",
            "search_index",
            "llm_call",
            "guardrail_check",
        }
        assert len(emitted) == len(trace.spans)

    def test_root_span_has_no_parent_and_the_rest_do(self):
        trace, _, _ = make_trace()
        handle_query("How is the warp core holding up?", trace)

        roots = [span for span in trace.spans if span["parent_id"] is None]
        assert len(roots) == 1
        assert roots[0]["name"] == "handle_request"
