"""Tests for Exercise 03 — Mission API."""

import pytest
import httpx

from start import create_app


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
async def client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestListMissions:
    @pytest.mark.asyncio
    async def test_returns_all_missions(self, client):
        r = await client.get("/missions")
        assert r.status_code == 200
        data = r.json()
        assert "count" in data
        assert "missions" in data
        assert data["count"] == len(data["missions"])
        assert data["count"] > 0

    @pytest.mark.asyncio
    async def test_filter_by_status(self, client):
        r = await client.get("/missions", params={"status": "active"})
        data = r.json()
        assert data["count"] > 0
        assert all(m["status"] == "active" for m in data["missions"])

    @pytest.mark.asyncio
    async def test_filter_returns_empty_for_unknown_status(self, client):
        r = await client.get("/missions", params={"status": "nonexistent"})
        data = r.json()
        assert data["count"] == 0
        assert data["missions"] == []


class TestGetMission:
    @pytest.mark.asyncio
    async def test_get_existing_mission(self, client):
        r = await client.get("/missions/MSN-001")
        assert r.status_code == 200
        assert r.json()["id"] == "MSN-001"
        assert "name" in r.json()

    @pytest.mark.asyncio
    async def test_get_missing_mission_returns_404(self, client):
        r = await client.get("/missions/MSN-999")
        assert r.status_code == 404


class TestCreateMission:
    @pytest.mark.asyncio
    async def test_create_new_mission(self, client):
        new_mission = {
            "id": "MSN-100",
            "name": "Test Mission",
            "sector": "Test Sector",
            "status": "planning",
            "crewSize": 4,
            "riskLevel": 2,
        }
        r = await client.post("/missions", json=new_mission)
        assert r.status_code == 201
        assert r.json()["id"] == "MSN-100"

        r2 = await client.get("/missions/MSN-100")
        assert r2.status_code == 200
        assert r2.json()["name"] == "Test Mission"


class TestUpdateMission:
    @pytest.mark.asyncio
    async def test_patch_existing_mission(self, client):
        r = await client.patch("/missions/MSN-001", json={"status": "completed"})
        assert r.status_code == 200
        assert r.json()["status"] == "completed"
        assert r.json()["id"] == "MSN-001"

    @pytest.mark.asyncio
    async def test_patch_missing_mission_returns_404(self, client):
        r = await client.patch("/missions/MSN-999", json={"status": "cancelled"})
        assert r.status_code == 404
