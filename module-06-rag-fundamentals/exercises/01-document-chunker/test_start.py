"""Tests for Exercise 01 — Document Chunker."""

import pytest

from start import chunk_logs


@pytest.mark.skip(reason="Skeleton — implement chunk_logs in start.py")
def test_chunk_logs_produces_windows():
    entries = [{"id": "L1", "message": "x" * 100}]
    chunks = chunk_logs(entries, chunk_size=30, overlap=10)
    assert len(chunks) >= 1
