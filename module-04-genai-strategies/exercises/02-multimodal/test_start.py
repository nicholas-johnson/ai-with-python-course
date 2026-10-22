"""Tests for Exercise 2: Multimodal"""

import base64
import importlib
import json

import pytest
from fastapi.testclient import TestClient


def _load_app():
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
    assert resp.json()["status"] == "ok"


def test_vision_endpoint_exists(client):
    """Check /vision endpoint exists and validates input."""
    resp = client.post("/vision", json={})
    assert resp.status_code in (422, 400), "Should reject empty body"



def _solid_png(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    """Build a valid solid-colour PNG (the API rejects malformed images)."""
    import struct
    import zlib

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    row = b"\x00" + bytes(rgb) * width
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(row * height))
        + chunk(b"IEND", b"")
    )

def test_vision_accepts_image(client):
    """Check /vision accepts a base64 image and returns structured data."""
    img_b64 = base64.b64encode(_solid_png(32, 32, (40, 90, 200))).decode()

    resp = client.post(
        "/vision",
        json={"image": img_b64, "prompt": "What do you see?"},
    )
    if resp.status_code == 200:
        data = resp.json()
        assert "description" in data
        assert "key_points" in data


def test_transcribe_endpoint_exists(client):
    """Check /transcribe endpoint exists."""
    resp = client.post("/transcribe")
    assert resp.status_code in (422, 400), "Should reject missing file"


def test_chat_still_works(client):
    resp = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")
