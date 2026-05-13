"""
Exercise 01 — Document Chunker
Chunk ship logs into overlapping windows for RAG indexing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TextChunk:
    """One retrievable slice of a ship log."""

    text: str
    source_id: str
    chunk_index: int


# TODO: Implement chunk_logs(log_entries, chunk_size: int, overlap: int) -> list[TextChunk]
# - Concatenate or iterate per entry; preserve source_id on each chunk.
# - Overlap means consecutive windows share trailing/leading characters.
# - chunk_index should be stable within each source (0, 1, 2, ...).


def chunk_logs(log_entries: list[dict[str, Any]], chunk_size: int, overlap: int) -> list[TextChunk]:
    raise NotImplementedError("TODO: implement chunking")
