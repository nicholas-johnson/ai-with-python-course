"""Tests for Exercise 02 — Streaming API."""

import json

import httpx
import pytest

from start import create_app, sessions


@pytest.fixture(autouse=True)
def clear_sessions():
    sessions.clear()
    yield
    sessions.clear()


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
async def client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestChatEndpoint:
    @pytest.mark.asyncio
    async def test_chat_returns_sse_stream(self, client):
        r = await client.post("/chat", json={"message": "Hello"})
        assert r.status_code == 200
        assert "text/event-stream" in r.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_chat_creates_session(self, client):
        r = await client.post("/chat", json={"message": "Hi", "session_id": "test-session"})
        assert r.status_code == 200
        assert "test-session" in sessions

    @pytest.mark.asyncio
    async def test_chat_appends_messages(self, client):
        await client.post("/chat", json={"message": "Hello", "session_id": "s1"})
        msgs = sessions.get("s1", [])
        roles = [m["role"] for m in msgs]
        assert "system" in roles
        assert "user" in roles
        assert "assistant" in roles


class TestSessionEndpoint:
    @pytest.mark.asyncio
    async def test_get_existing_session(self, client):
        await client.post("/chat", json={"message": "test", "session_id": "s1"})
        r = await client.get("/sessions/s1")
        assert r.status_code == 200
        data = r.json()
        assert data["session_id"] == "s1"
        assert len(data["messages"]) >= 2

    @pytest.mark.asyncio
    async def test_get_missing_session_returns_404(self, client):
        r = await client.get("/sessions/nonexistent")
        assert r.status_code == 404
