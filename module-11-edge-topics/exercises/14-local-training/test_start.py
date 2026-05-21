"""Tests for Exercise 14 — Local Training."""

import json
from pathlib import Path

import pytest

from start import (
    build_dataset,
    load_examples,
    predict,
    train_model,
)

DATA_PATH = Path(__file__).parent / "data" / "labels.json"
# Tiny model for fast CPU tests (~4M params)
TEST_MODEL = "prajjwal1/bert-tiny"


@pytest.fixture
def examples():
    return load_examples(DATA_PATH)


class TestLoadExamples:
    def test_loads_json(self):
        data = load_examples(DATA_PATH)
        assert len(data) >= 20
        assert "text" in data[0] and "label" in data[0]

    def test_invalid_label_raises(self, tmp_path):
        bad = [{"text": "test", "label": "invalid"}]
        path = tmp_path / "bad.json"
        path.write_text(json.dumps(bad), encoding="utf-8")
        with pytest.raises(ValueError):
            load_examples(path)


class TestBuildDataset:
    def test_returns_dataset_with_labels(self, examples):
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(TEST_MODEL)
        ds = build_dataset(examples, tokenizer)
        assert "input_ids" in ds.column_names
        assert "labels" in ds.column_names
        assert len(ds) == len(examples)


class TestTrainAndPredict:
    def test_train_saves_model(self, examples, tmp_path):
        out = tmp_path / "model"
        train_model(
            examples,
            out,
            model_name=TEST_MODEL,
            max_steps=2,
        )
        assert (out / "config.json").exists()

    def test_predict_returns_valid_label(self, examples, tmp_path):
        out = tmp_path / "model"
        train_model(
            examples,
            out,
            model_name=TEST_MODEL,
            max_steps=2,
        )
        label = predict(out, "Reactor coolant pressure stable.")
        assert label in {"engineering", "medical", "navigation"}
