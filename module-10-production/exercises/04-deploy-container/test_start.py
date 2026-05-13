"""Tests for Exercise 04 — Deploy Container."""

from __future__ import annotations

import os

import pytest

from start import create_app, load_config, validate_dockerfile


class TestCreateApp:
    def test_health_endpoint_exists(self):
        app = create_app()
        routes = [r.path for r in app.routes]
        assert "/health" in routes

    @pytest.mark.asyncio
    async def test_health_returns_ok(self):
        import httpx

        app = create_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestLoadConfig:
    def test_loads_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
        config = load_config()
        assert config["openai_api_key"] == "sk-test-123"

    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            load_config()

    def test_default_model(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        config = load_config()
        assert config["model"] == "gpt-4o-mini"

    def test_custom_model(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
        config = load_config()
        assert config["model"] == "gpt-4o"

    def test_default_port(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("PORT", raising=False)
        config = load_config()
        assert config["port"] == 8000

    def test_debug_true(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("DEBUG", "true")
        config = load_config()
        assert config["debug"] is True

    def test_debug_false_by_default(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("DEBUG", raising=False)
        config = load_config()
        assert config["debug"] is False


class TestValidateDockerfile:
    def test_complete_dockerfile(self):
        dockerfile = (
            "FROM python:3.12-slim\n"
            "EXPOSE 8000\n"
            "HEALTHCHECK CMD curl localhost\n"
            "CMD [\"uvicorn\", \"app:app\"]\n"
        )
        assert validate_dockerfile(dockerfile) == []

    def test_missing_healthcheck(self):
        dockerfile = "FROM python:3.12\nEXPOSE 8000\nCMD uvicorn app:app\n"
        missing = validate_dockerfile(dockerfile)
        assert "HEALTHCHECK" in missing

    def test_missing_multiple(self):
        dockerfile = "FROM python:3.12\n"
        missing = validate_dockerfile(dockerfile)
        assert "EXPOSE" in missing
        assert "HEALTHCHECK" in missing
        assert "CMD" in missing

    def test_empty_dockerfile(self):
        missing = validate_dockerfile("")
        assert len(missing) == 4
