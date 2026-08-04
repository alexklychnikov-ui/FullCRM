import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.config import Settings
from app.main import create_app
from app.db.session import (
    DatabaseNotConfiguredError,
    clear_session_cache,
    create_session_factory,
    get_db_session,
    get_session_factory,
)


def test_session_factory_is_cached_per_database_url() -> None:
    database_url = "sqlite+pysqlite:///:memory:"

    clear_session_cache()

    try:
        first_factory = get_session_factory(database_url)
        second_factory = get_session_factory(database_url)

        assert first_factory is second_factory
        assert first_factory.kw["bind"] is second_factory.kw["bind"]
    finally:
        clear_session_cache()


def test_explicit_engine_session_factory_is_not_global_cached() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    try:
        first_factory = create_session_factory(engine)
        second_factory = create_session_factory(engine)

        assert first_factory is not second_factory
        assert first_factory.kw["bind"] is engine
        assert second_factory.kw["bind"] is engine
    finally:
        engine.dispose()


def test_get_db_session_returns_service_unavailable_when_database_is_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    clear_session_cache()
    session_generator = get_db_session()

    try:
        with pytest.raises(DatabaseNotConfiguredError) as error:
            next(session_generator)

        assert str(error.value) == "Database is not configured"
    finally:
        clear_session_cache()


def test_database_not_configured_error_is_rendered_as_service_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    clear_session_cache()
    app = create_app(
        Settings(
            app_env="test",
            api_cors_origins=("http://localhost:3000",),
        )
    )

    @app.get("/db-check")
    def db_check(session=Depends(get_db_session)) -> dict[str, bool]:
        _ = session
        return {"ok": True}

    try:
        with TestClient(app) as client:
            response = client.get("/db-check")

        assert response.status_code == 503
        assert response.json() == {"detail": "Database is not configured"}
    finally:
        clear_session_cache()
