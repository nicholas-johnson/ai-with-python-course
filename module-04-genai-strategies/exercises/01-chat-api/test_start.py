"""Tests for Exercise 1: Streaming Chat API"""

import json
import importlib
import pytest
from fastapi.testclient import TestClient


def _load_app():
    """Try solution first, fall back to start."""
    for module_name in ("solution", "start"):
        try:
            mod = importlib.import_module(module_name)
            return mod.app
        except (ImportError, AttributeError):
            continue
    pytest.skip("No app found in solution.py or start.py")


@pytest.fixture
def client():
    app = _load_app()
    return TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_chat_returns_sse(client):
    resp = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "Say hello in one word."}]},
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")


def test_chat_has_done_event(client):
    resp = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "Say hello in one word."}]},
    )
    body = resp.text

    has_token = "event: token" in body
    has_done = "event: done" in body

    assert has_token, "Expected at least one 'token' SSE event"
    assert has_done, "Expected a 'done' SSE event"

    for line in body.splitlines():
        if line.startswith("data: ") and "done" not in body.splitlines()[
            body.splitlines().index(line) - 1
        ]:
            continue
        if line.startswith("data: {"):
            data = json.loads(line[6:])
            if "role" in data:
                assert data["role"] == "assistant"
                assert len(data["content"]) > 0
                break


def test_chat_validates_body(client):
    resp = client.post("/chat", json={})
    assert resp.status_code == 422
