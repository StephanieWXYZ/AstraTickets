from fastapi.testclient import TestClient

from app.core.config import get_settings


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_local_frontend_is_an_allowed_origin() -> None:
    assert "http://localhost:5173" in get_settings().allowed_origins
