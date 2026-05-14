"""Tests for Exercise 2: RAG Chat."""

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


def _import_start():
    """Import start.py (or solution.py as fallback) as a module."""
    ex_dir = Path(__file__).resolve().parent
    for name in ("start", "solution"):
        mod_path = ex_dir / f"{name}.py"
        if mod_path.exists():
            spec = importlib.util.spec_from_file_location(name, mod_path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            return mod
    raise FileNotFoundError("Neither start.py nor solution.py found")


def test_build_grounded_prompt_structure():
    """build_grounded_prompt returns system + user messages with source labels."""
    mod = _import_start()

    passages = [
        {"text": "Hull breach detected in sector 7.", "metadata": {"source_id": "LOG-015"}},
        {"text": "Emergency teams dispatched.", "metadata": {"source_id": "LOG-015"}},
    ]
    messages = mod.build_grounded_prompt("What happened in sector 7?", passages)

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "[Source 1:" in messages[1]["content"]
    assert "[Source 2:" in messages[1]["content"]
    assert "sector 7" in messages[1]["content"]


def test_build_grounded_prompt_cites_sources():
    """Prompt includes all passage texts with source labels."""
    mod = _import_start()

    passages = [
        {"text": "Alpha passage content.", "metadata": {"source_id": "DOC-A"}},
        {"text": "Beta passage content.", "metadata": {"source_id": "DOC-B"}},
        {"text": "Gamma passage content.", "metadata": {"source_id": "DOC-C"}},
    ]
    messages = mod.build_grounded_prompt("Test question?", passages)

    user_content = messages[1]["content"]
    assert "Alpha passage content" in user_content
    assert "Beta passage content" in user_content
    assert "Gamma passage content" in user_content
    assert "DOC-A" in user_content
    assert "DOC-B" in user_content
    assert "DOC-C" in user_content


def test_rag_chat_returns_answer_and_passages():
    """rag_chat returns a (str, list) tuple."""
    mod = _import_start()

    mock_collection = MagicMock()

    fake_passages = [
        {"id": "c0", "text": "Some text.", "distance": 0.1, "metadata": {"source_id": "LOG-001"}},
    ]

    with patch.object(mod, "search", return_value=fake_passages) as mock_search:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="The answer is 42."))]

        with patch.object(mod, "client", create=True) as mock_client:
            mock_client.chat.completions.create.return_value = mock_response
            answer, passages = mod.rag_chat("test?", mock_collection, k=3)

    assert isinstance(answer, str)
    assert len(answer) > 0
    assert isinstance(passages, list)
    mock_search.assert_called_once_with(mock_collection, "test?", 3)
