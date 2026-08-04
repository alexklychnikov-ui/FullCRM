from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


class FailingSession:
    def __enter__(self) -> "FailingSession":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        _ = exc_type
        _ = exc
        _ = traceback

    def execute(self, statement: object) -> None:
        _ = statement
        raise RuntimeError("database unavailable")


def failing_session_factory() -> FailingSession:
    return FailingSession()


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


def test_liveness_returns_ok_without_database() -> None:
    settings = Settings(
        app_env="test",
        api_cors_origins=("http://localhost:3000",),
    )
    client = TestClient(create_app(settings))

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_requires_database_configuration() -> None:
    settings = Settings(
        app_env="test",
        api_cors_origins=("http://localhost:3000",),
    )
    client = TestClient(create_app(settings))

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "error",
        "checks": {"database": "not_configured"},
    }


def test_readiness_reports_database_ok() -> None:
    settings = Settings(
        app_env="test",
        api_cors_origins=("http://localhost:3000",),
        database_url="sqlite+pysqlite:///:memory:",
    )
    client = TestClient(create_app(settings))

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {"database": "ok"},
    }


def test_readiness_reports_database_unavailable() -> None:
    settings = Settings(
        app_env="test",
        api_cors_origins=("http://localhost:3000",),
        database_url="sqlite+pysqlite:///:memory:",
    )

    with TestClient(create_app(settings)) as client:
        client.app.state.session_factory = failing_session_factory

        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "error",
        "checks": {"database": "unavailable"},
    }
