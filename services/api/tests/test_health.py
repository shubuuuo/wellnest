from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_route_uses_unified_error_shape():
    response = client.get("/api/v1/nope")
    assert response.status_code == 404
    body = response.json()
    assert set(body) == {"code", "message", "details"}
    assert body["code"] == "HTTP_404"


def test_cors_allows_web_origin_with_credentials():
    response = client.get("/api/v1/health", headers={"Origin": "http://localhost:3000"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert response.headers["access-control-allow-credentials"] == "true"