from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_health_returns_service_status() -> None:
    settings = Settings(
        app_env="test",
        api_cors_origins=("http://localhost:3000",),
    )
    client = TestClient(create_app(settings))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "fullcrm-api",
        "environment": "test",
    }
