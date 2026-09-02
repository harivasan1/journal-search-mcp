from fastapi.testclient import TestClient

from fastapi_app import app

client = TestClient(app)


def test_concepts_success(monkeypatch):
    monkeypatch.setattr(
        "services.openalex.search_concepts",
        lambda query, per_page=10: [
            {"id": "C1", "name": "Machine Learning", "level": 1, "works_count": 12345}
        ],
    )
    r = client.get("/concepts", params={"query": "machine"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert data[0]["name"] == "Machine Learning"


def test_concepts_validation(monkeypatch):
    r = client.get("/concepts", params={"query": "  "})
    assert r.status_code == 400
