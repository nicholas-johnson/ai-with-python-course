"""Tests for the Movie Night FastAPI app."""


def test_health(app_client):
    response = app_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["movies_loaded"] == 3


def test_recommend(app_client):
    response = app_client.post("/api/recommend", json={"query": "something uplifting"})
    assert response.status_code == 200
    data = response.json()
    assert "movies" in data
    assert "trace" in data


def test_query(app_client):
    response = app_client.post("/api/query", json={"question": "How many movies are there?"})
    assert response.status_code == 200
    data = response.json()
    assert "sql" in data
    assert "rows" in data
    assert "row_count" in data


def test_movie_by_id(app_client):
    response = app_client.get("/api/movie/1")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "The Shawshank Redemption"


def test_movie_not_found(app_client):
    response = app_client.get("/api/movie/9999")
    assert response.status_code == 404
