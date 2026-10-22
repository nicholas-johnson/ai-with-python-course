"""Tests for Exercise 01 — Chain Basics."""

import os

import pytest
from start import classify_report


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
def test_classify_report_returns_expected_keys():
    result = classify_report("Hull breach detected on deck 7, requesting engineering team.")
    assert isinstance(result, dict)
    assert result["category"] in {"navigation", "engineering", "science", "medical", "operations"}
    assert isinstance(result["summary"], str) and result["summary"]
    assert result["priority"] in {"low", "medium", "high", "critical"}


def test_classification_schema_restricts_values():
    """If you defined a Classification model, it should reject unknown categories."""
    import start

    if not hasattr(start, "Classification"):
        pytest.skip("Classification model not defined yet")
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        start.Classification(category="cooking", summary="x", priority="low")
