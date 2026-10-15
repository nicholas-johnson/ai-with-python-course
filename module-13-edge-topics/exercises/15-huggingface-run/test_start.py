"""Tests for Exercise 15 — Hugging Face Run."""

from pathlib import Path

import pytest

from start import classify, classify_batch, load_model

# Tiny random weights — no download, fast offline tests
TEST_MODEL = "hf-internal-testing/tiny-random-DistilBertForSequenceClassification"
LOGS_PATH = Path(__file__).parent / "data" / "logs.txt"


@pytest.fixture(scope="module")
def model_bundle():
    return load_model(TEST_MODEL)


class TestLoadModel:
    def test_returns_tokenizer_and_model(self, model_bundle):
        tokenizer, model = model_bundle
        assert tokenizer is not None
        assert model is not None


class TestClassify:
    def test_classify_returns_dict(self, model_bundle):
        tokenizer, model = model_bundle
        result = classify("Test log line.", tokenizer, model)
        assert "label" in result
        assert "score" in result
        assert 0.0 <= result["score"] <= 1.0

    def test_classify_batch_length(self, model_bundle):
        tokenizer, model = model_bundle
        texts = ["Line one.", "Line two.", "Line three."]
        results = classify_batch(texts, tokenizer, model)
        assert len(results) == 3
        assert all("label" in r and "score" in r for r in results)

    def test_logs_file_readable(self):
        lines = LOGS_PATH.read_text(encoding="utf-8").splitlines()
        assert len([ln for ln in lines if ln.strip()]) >= 5
