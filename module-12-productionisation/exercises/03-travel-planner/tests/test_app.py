"""Tests for the travel planner API."""

import json
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from solution.tools import get_weather, estimate_budget, estimate_travel_time
from solution.guardrails import validate_budget, check_safety


class TestTools:
    def test_get_weather_returns_data(self):
        result = get_weather("Tokyo")
        assert "city" in result
        assert result["city"] == "Tokyo"
        assert "temp_c" in result
        assert "condition" in result
        assert "forecast" in result
        assert len(result["forecast"]) == 5

    def test_get_weather_deterministic(self):
        r1 = get_weather("Paris")
        r2 = get_weather("Paris")
        assert r1["temp_c"] == r2["temp_c"]

    def test_estimate_budget(self):
        result = estimate_budget(["museum", "restaurant"], "moderate")
        assert result["budget_level"] == "moderate"
        assert result["daily_estimate_usd"] > 0
        assert "breakdown" in result
        assert result["num_activities"] == 2

    def test_estimate_travel_time(self):
        result = estimate_travel_time("Hotel", "Museum")
        assert result["from"] == "Hotel"
        assert result["to"] == "Museum"
        assert 10 <= result["duration_minutes"] <= 90
        assert result["mode"] in ("taxi", "public transport")


class TestGuardrails:
    def test_validate_budget_within_limits(self):
        itinerary = [
            {"day": 1, "estimated_cost_usd": 100},
            {"day": 2, "estimated_cost_usd": 120},
        ]
        result = validate_budget(itinerary, "moderate")
        assert result["valid"] is True
        assert result["warnings"] == []

    def test_validate_budget_exceeds_limit(self):
        itinerary = [
            {"day": 1, "estimated_cost_usd": 500},
        ]
        result = validate_budget(itinerary, "budget")
        assert result["valid"] is False
        assert len(result["warnings"]) == 1

    def test_check_safety_clean(self):
        dest = {"name": "Paris", "description": "Beautiful city", "safety_notes": ""}
        result = check_safety(dest)
        assert result["safe"] is True
        assert result["advisories"] == []

    def test_check_safety_flagged(self):
        dest = {"name": "Danger Zone", "description": "active conflict area", "safety_notes": ""}
        result = check_safety(dest)
        assert result["safe"] is False
        assert len(result["advisories"]) > 0


class TestHealthEndpoint:
    def test_health(self):
        with patch("solution.app.startup"):
            from solution.app import app, destinations, collection
            import solution.app as app_module
            app_module.destinations = [{"id": "test"}]
            app_module.collection = MagicMock()

            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/api/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["destinations_loaded"] == 1
            assert data["index_ready"] is True


class TestSearchEndpoint:
    def test_search(self):
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "documents": [["Tokyo — vibrant city"]],
            "ids": [["dest_tokyo"]],
            "metadatas": [[{"type": "destination", "dest_id": "tokyo", "name": "Tokyo", "country": "Japan"}]],
            "distances": [[0.2]],
        }

        with patch("solution.app.startup"), \
             patch("solution.app.collection", mock_collection), \
             patch("solution.rag.get_embedding", return_value=[0.1] * 1536):
            from solution.app import app
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/api/search", json={"query": "temples"})
            assert response.status_code == 200
            data = response.json()
            assert "results" in data


class TestDestinationEndpoint:
    def test_destination_by_id(self):
        import solution.app as app_module
        app_module.destinations = [
            {"id": "tokyo", "name": "Tokyo", "country": "Japan"},
        ]

        with patch("solution.app.startup"):
            from solution.app import app
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/api/destination/tokyo")
            assert response.status_code == 200
            assert response.json()["name"] == "Tokyo"

    def test_destination_not_found(self):
        import solution.app as app_module
        app_module.destinations = []

        with patch("solution.app.startup"):
            from solution.app import app
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/api/destination/nonexistent")
            assert response.status_code == 404
