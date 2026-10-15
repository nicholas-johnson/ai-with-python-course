"""Tests for Exercise 13 — Contextual Chunking."""

from start import fixed_chunk, overlap_chunk, parent_child_chunk, retrieve_with_context


SAMPLE_TEXT = " ".join(f"word{i}" for i in range(500))


class TestFixedChunk:
    def test_returns_list_of_strings(self):
        chunks = fixed_chunk(SAMPLE_TEXT, chunk_size=100)
        assert isinstance(chunks, list)
        assert all(isinstance(c, str) for c in chunks)

    def test_correct_number_of_chunks(self):
        chunks = fixed_chunk(SAMPLE_TEXT, chunk_size=100)
        assert len(chunks) == 5

    def test_chunk_sizes(self):
        chunks = fixed_chunk(SAMPLE_TEXT, chunk_size=100)
        for chunk in chunks:
            assert len(chunk.split()) <= 100

    def test_no_empty_chunks(self):
        chunks = fixed_chunk(SAMPLE_TEXT, chunk_size=100)
        assert all(len(c.strip()) > 0 for c in chunks)

    def test_preserves_all_words(self):
        chunks = fixed_chunk(SAMPLE_TEXT, chunk_size=100)
        reconstructed = " ".join(chunks)
        assert reconstructed == SAMPLE_TEXT

    def test_small_text(self):
        chunks = fixed_chunk("hello world", chunk_size=100)
        assert len(chunks) == 1
        assert chunks[0] == "hello world"


class TestOverlapChunk:
    def test_returns_list(self):
        chunks = overlap_chunk(SAMPLE_TEXT, chunk_size=100, overlap=20)
        assert isinstance(chunks, list)

    def test_more_chunks_than_fixed(self):
        fixed = fixed_chunk(SAMPLE_TEXT, chunk_size=100)
        overlapping = overlap_chunk(SAMPLE_TEXT, chunk_size=100, overlap=20)
        assert len(overlapping) >= len(fixed)

    def test_overlap_present(self):
        chunks = overlap_chunk(SAMPLE_TEXT, chunk_size=10, overlap=3)
        if len(chunks) >= 2:
            words1 = set(chunks[0].split())
            words2 = set(chunks[1].split())
            assert len(words1 & words2) > 0

    def test_no_empty_chunks(self):
        chunks = overlap_chunk(SAMPLE_TEXT, chunk_size=100, overlap=20)
        assert all(len(c.strip()) > 0 for c in chunks)


class TestParentChildChunk:
    def test_returns_list_of_dicts(self):
        chunks = parent_child_chunk(SAMPLE_TEXT, parent_size=200, child_size=50)
        assert isinstance(chunks, list)
        assert all(isinstance(c, dict) for c in chunks)

    def test_has_required_keys(self):
        chunks = parent_child_chunk(SAMPLE_TEXT, parent_size=200, child_size=50)
        for chunk in chunks:
            assert "child_text" in chunk
            assert "parent_id" in chunk
            assert "parent_text" in chunk

    def test_children_belong_to_parents(self):
        chunks = parent_child_chunk(SAMPLE_TEXT, parent_size=200, child_size=50)
        for chunk in chunks:
            assert chunk["child_text"] in chunk["parent_text"]

    def test_multiple_parents(self):
        chunks = parent_child_chunk(SAMPLE_TEXT, parent_size=200, child_size=50)
        parent_ids = set(c["parent_id"] for c in chunks)
        assert len(parent_ids) >= 2

    def test_children_per_parent(self):
        chunks = parent_child_chunk(SAMPLE_TEXT, parent_size=200, child_size=50)
        parent_0_children = [c for c in chunks if c["parent_id"] == 0]
        assert len(parent_0_children) == 4

    def test_no_empty_children(self):
        chunks = parent_child_chunk(SAMPLE_TEXT, parent_size=200, child_size=50)
        assert all(len(c["child_text"].strip()) > 0 for c in chunks)


class TestRetrieveWithContext:
    def test_returns_unique_parents(self):
        children = [
            {"child_text": "c1", "parent_id": 0, "parent_text": "parent 0", "embedding": [0.9, 0.1]},
            {"child_text": "c2", "parent_id": 0, "parent_text": "parent 0", "embedding": [0.8, 0.2]},
            {"child_text": "c3", "parent_id": 1, "parent_text": "parent 1", "embedding": [0.1, 0.9]},
        ]
        results = retrieve_with_context([0.9, 0.1], children, top_k=2)
        parent_ids = [r["parent_id"] for r in results]
        assert len(parent_ids) == len(set(parent_ids))

    def test_ranked_by_score(self):
        children = [
            {"child_text": "c1", "parent_id": 0, "parent_text": "P0", "embedding": [0.9, 0.1]},
            {"child_text": "c2", "parent_id": 1, "parent_text": "P1", "embedding": [0.1, 0.9]},
        ]
        results = retrieve_with_context([0.9, 0.1], children, top_k=2)
        assert results[0]["best_child_score"] >= results[1]["best_child_score"]

    def test_respects_top_k(self):
        children = [
            {"child_text": f"c{i}", "parent_id": i, "parent_text": f"P{i}", "embedding": [0.1 * i, 0.9]}
            for i in range(10)
        ]
        results = retrieve_with_context([0.5, 0.5], children, top_k=3)
        assert len(results) == 3

    def test_returns_parent_text(self):
        children = [
            {"child_text": "child", "parent_id": 0, "parent_text": "Full parent text here", "embedding": [1.0, 0.0]},
        ]
        results = retrieve_with_context([1.0, 0.0], children, top_k=1)
        assert results[0]["parent_text"] == "Full parent text here"

    def test_best_child_score_is_highest(self):
        children = [
            {"child_text": "c1", "parent_id": 0, "parent_text": "P0", "embedding": [0.5, 0.5]},
            {"child_text": "c2", "parent_id": 0, "parent_text": "P0", "embedding": [0.9, 0.1]},
        ]
        results = retrieve_with_context([0.9, 0.1], children, top_k=1)
        assert results[0]["best_child_score"] > 0.9
