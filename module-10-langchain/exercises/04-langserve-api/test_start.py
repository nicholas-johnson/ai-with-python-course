"""Tests for Exercise 04 — LangServe API."""

import os

import httpx
import pytest

from start import create_app


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
async def client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_returns_ok(self, client):
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


class TestLangServeRoutes:
    @pytest.mark.asyncio
    async def test_classify_invoke_route_registered(self, client):
        r = await client.get("/openapi.json")
        assert r.status_code == 200
        paths = r.json()["paths"]
        assert "/classify/invoke" in paths


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
class TestClassifyInvoke:
    @pytest.mark.asyncio
    async def test_invoke_returns_classification(self, client):
        r = await client.post(
            "/classify/invoke",
            json={
                "input": {
                    "report": "Hull breach detected on deck 7, requesting engineering team.",
                }
            },
            timeout=60.0,
        )
        assert r.status_code == 200
        data = r.json()
        output = data.get("output", data)
        assert "category" in output
        assert "summary" in output
        assert "priority" in output
