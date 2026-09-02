from fastapi.testclient import TestClient

from fastapi_app import app
from utils.exceptions import APIRequestError

client = TestClient(app)


def test_ready_healthy(monkeypatch):
    # Simulate both upstream services returning successfully
    def fake_get_json(url, params=None, headers=None, service="default", **kwargs):
        return {"results": []}

    monkeypatch.setattr("fastapi_app.get_json", fake_get_json)

    r = client.get("/ready")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ready"
    assert j["services"]["openalex"]["ok"] is True
    assert j["services"]["crossref"]["ok"] is True


def test_ready_openalex_unhealthy(monkeypatch):
    # Simulate OpenAlex failing while Crossref is reachable
    def fake_get_json(url, params=None, headers=None, service="default", **kwargs):
        if service == "openalex":
            raise APIRequestError("unavailable")
        return {"results": []}

    monkeypatch.setattr("fastapi_app.get_json", fake_get_json)

    r = client.get("/ready")
    assert r.status_code == 503
    detail = r.json().get("detail")
    assert detail is not None
    assert detail["openalex"]["ok"] is False
    assert "error" in detail["openalex"]
    assert detail["crossref"]["ok"] is True
