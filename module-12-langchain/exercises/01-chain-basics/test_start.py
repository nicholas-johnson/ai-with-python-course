"""Tests for Exercise 01 — Chain Basics."""

import pytest

from start import classify_report


@pytest.mark.skip(reason="Skeleton — implement classify_report")
def test_classify_report_returns_expected_keys():
    result = classify_report("Hull breach detected on deck 7, requesting engineering team.")
    assert isinstance(result, dict)
    assert "category" in result
    assert "summary" in result
    assert "priority" in result
