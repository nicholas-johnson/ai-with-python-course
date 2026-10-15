"""Tests for Exercise 06 — Web Search Backend."""

from unittest.mock import MagicMock, patch
from start import format_web_results, search_with_fallback


RAW_WEB_RESULTS = [
    {"title": "Reactor Safety Guide", "snippet": "How to maintain reactor safety.", "url": "https://example.com/1"},
    {"title": "Hull Repair Manual", "snippet": "Steps for hull repair.", "url": "https://example.com/2"},
]


class TestFormatWebResults:
    def test_returns_list_of_dicts(self):
        results = format_web_results(RAW_WEB_RESULTS)
        assert isinstance(results, list)
        assert len(results) == 2

    def test_has_text_key(self):
        results = format_web_results(RAW_WEB_RESULTS)
        for r in results:
            assert "text" in r
            assert isinstance(r["text"], str)
            assert len(r["text"]) > 0

    def test_text_combines_title_and_snippet(self):
        results = format_web_results(RAW_WEB_RESULTS)
        assert "Reactor Safety Guide" in results[0]["text"]
        assert "maintain reactor safety" in results[0]["text"]

    def test_has_source_web(self):
        results = format_web_results(RAW_WEB_RESULTS)
        for r in results:
            assert r["source"] == "web"

    def test_has_url(self):
        results = format_web_results(RAW_WEB_RESULTS)
        assert results[0]["url"] == "https://example.com/1"

    def test_empty_input(self):
        results = format_web_results([])
        assert results == []


class TestSearchWithFallback:
    def test_returns_internal_when_above_threshold(self):
        internal = [{"text": "Relevant doc", "score": 0.9}]
        vector_fn = MagicMock(return_value=internal)

        result = search_with_fallback("query", vector_fn, threshold=0.7)
        assert result["source"] == "internal"
        assert result["results"] == internal

    def test_falls_back_when_below_threshold(self):
        internal = [{"text": "Weak match", "score": 0.3}]
        vector_fn = MagicMock(return_value=internal)

        with patch("start.web_search", return_value=RAW_WEB_RESULTS):
            result = search_with_fallback("query", vector_fn, threshold=0.7)
            assert result["source"] == "web"
            assert len(result["results"]) > 0

    def test_falls_back_when_no_internal_results(self):
        vector_fn = MagicMock(return_value=[])

        with patch("start.web_search", return_value=RAW_WEB_RESULTS):
            result = search_with_fallback("query", vector_fn, threshold=0.7)
            assert result["source"] == "web"

    def test_returns_dict_with_source_key(self):
        vector_fn = MagicMock(return_value=[{"text": "doc", "score": 0.95}])
        result = search_with_fallback("q", vector_fn)
        assert "source" in result
        assert "results" in result
