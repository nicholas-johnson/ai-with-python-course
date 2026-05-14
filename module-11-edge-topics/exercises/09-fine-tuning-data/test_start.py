"""Tests for Exercise 09 — Fine-tuning Data Preparation."""

import json
import os
import tempfile
import pytest
from start import format_example, prepare_dataset, write_jsonl, validate_jsonl


SYSTEM_PROMPT = "You are a helpful assistant."

EXAMPLES = [
    {"input": "What is the reactor status?", "output": "The reactor is stable at 5000K."},
    {"input": "How many crew members?", "output": "There are 42 crew members aboard."},
    {"input": "What deck is engineering?", "output": "Engineering is on deck 3."},
    {"input": "Navigation status?", "output": "All navigation systems are nominal."},
    {"input": "Hull integrity?", "output": "Hull integrity is at 98%."},
    {"input": "Fuel reserves?", "output": "Fuel reserves are at 73%."},
    {"input": "Life support?", "output": "Life support is fully operational."},
    {"input": "Shield status?", "output": "Shields are at 100%."},
    {"input": "Communication range?", "output": "Comms range is 500 AU."},
    {"input": "Next port?", "output": "Next scheduled port is Station Omega."},
]


class TestFormatExample:
    def test_returns_dict_with_messages(self):
        result = format_example(EXAMPLES[0], SYSTEM_PROMPT)
        assert isinstance(result, dict)
        assert "messages" in result

    def test_messages_has_three_entries(self):
        result = format_example(EXAMPLES[0], SYSTEM_PROMPT)
        assert len(result["messages"]) == 3

    def test_correct_roles(self):
        result = format_example(EXAMPLES[0], SYSTEM_PROMPT)
        roles = [m["role"] for m in result["messages"]]
        assert roles == ["system", "user", "assistant"]

    def test_system_message_content(self):
        result = format_example(EXAMPLES[0], SYSTEM_PROMPT)
        assert result["messages"][0]["content"] == SYSTEM_PROMPT

    def test_user_message_content(self):
        result = format_example(EXAMPLES[0], SYSTEM_PROMPT)
        assert result["messages"][1]["content"] == EXAMPLES[0]["input"]

    def test_assistant_message_content(self):
        result = format_example(EXAMPLES[0], SYSTEM_PROMPT)
        assert result["messages"][2]["content"] == EXAMPLES[0]["output"]


class TestPrepareDataset:
    def test_returns_train_and_val(self):
        result = prepare_dataset(EXAMPLES, SYSTEM_PROMPT, val_fraction=0.2)
        assert "train" in result
        assert "val" in result

    def test_split_sizes(self):
        result = prepare_dataset(EXAMPLES, SYSTEM_PROMPT, val_fraction=0.2)
        assert len(result["train"]) == 8
        assert len(result["val"]) == 2

    def test_all_examples_formatted(self):
        result = prepare_dataset(EXAMPLES, SYSTEM_PROMPT, val_fraction=0.0)
        assert len(result["train"]) == 10
        for entry in result["train"]:
            assert "messages" in entry

    def test_zero_val_fraction(self):
        result = prepare_dataset(EXAMPLES, SYSTEM_PROMPT, val_fraction=0.0)
        assert len(result["val"]) == 0


class TestWriteJsonl:
    def test_writes_file(self):
        data = [{"messages": [{"role": "user", "content": "hi"}]}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            count = write_jsonl(data, path)
            assert count == 1
            assert os.path.exists(path)
        finally:
            os.unlink(path)

    def test_returns_count(self):
        data = [{"a": 1}, {"a": 2}, {"a": 3}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            count = write_jsonl(data, path)
            assert count == 3
        finally:
            os.unlink(path)

    def test_each_line_is_valid_json(self):
        data = [
            {"messages": [{"role": "user", "content": "q1"}]},
            {"messages": [{"role": "user", "content": "q2"}]},
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            write_jsonl(data, path)
            with open(path) as f:
                for line in f:
                    parsed = json.loads(line.strip())
                    assert "messages" in parsed
        finally:
            os.unlink(path)


class TestValidateJsonl:
    def test_valid_file(self):
        data = [format_example(ex, SYSTEM_PROMPT) for ex in EXAMPLES[:3]]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name
            for entry in data:
                f.write(json.dumps(entry) + "\n")
        try:
            result = validate_jsonl(path)
            assert result["valid"] is True
            assert result["num_examples"] == 3
            assert result["errors"] == []
        finally:
            os.unlink(path)

    def test_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name
            f.write("not valid json\n")
        try:
            result = validate_jsonl(path)
            assert result["valid"] is False
            assert len(result["errors"]) > 0
        finally:
            os.unlink(path)

    def test_missing_messages_key(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name
            f.write(json.dumps({"data": "no messages"}) + "\n")
        try:
            result = validate_jsonl(path)
            assert result["valid"] is False
        finally:
            os.unlink(path)

    def test_too_few_messages(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name
            entry = {"messages": [{"role": "user", "content": "hi"}]}
            f.write(json.dumps(entry) + "\n")
        try:
            result = validate_jsonl(path)
            assert result["valid"] is False
        finally:
            os.unlink(path)
