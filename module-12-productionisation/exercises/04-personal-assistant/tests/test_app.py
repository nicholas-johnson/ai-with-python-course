"""Tests for the personal assistant API."""

import json
from unittest.mock import AsyncMock, MagicMock, patch


def test_health(test_client):
    response = test_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["assistant"] == "Compass"


def test_calendar_list(test_client):
    response = test_client.get("/api/calendar")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert isinstance(data["events"], list)
    assert len(data["events"]) > 0


def test_calendar_create(test_client):
    new_event = {
        "title": "Test meeting",
        "date": "2025-04-01",
        "time": "10:00",
        "duration": 30,
        "location": "Zoom",
        "notes": "Test event",
    }
    response = test_client.post("/api/calendar", json=new_event)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "Test meeting" in data["result"]


def test_calendar_delete(test_client):
    response = test_client.delete("/api/calendar/event-001")
    assert response.status_code == 200
    data = response.json()
    assert "result" in data


def test_reminders_list(test_client):
    response = test_client.get("/api/reminders")
    assert response.status_code == 200
    data = response.json()
    assert "reminders" in data
    assert isinstance(data["reminders"], list)


def test_notes_search(test_client):
    response = test_client.get("/api/notes/search", params={"q": "meeting"})
    assert response.status_code == 200
    data = response.json()
    assert "results" in data


@patch("solution.agent.client")
def test_chat_returns_response(mock_openai, test_client):
    mock_choice = MagicMock()
    mock_choice.finish_reason = "stop"
    mock_choice.message.content = "Hello Alex! How can I help?"
    mock_choice.message.tool_calls = None

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_openai.chat.completions.create.return_value = mock_response

    response = test_client.post(
        "/api/chat",
        json={"message": "Hello!", "history": []},
    )
    assert response.status_code == 200
