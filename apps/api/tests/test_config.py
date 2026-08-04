import pytest

from app.config import DEFAULT_LOCAL_CORS_ORIGINS, Settings, parse_cors_origins


def test_parse_cors_origins_from_comma_separated_env() -> None:
    origins = parse_cors_origins(
        "http://localhost:3000, https://crm.example.com ,"
    )

    assert origins == ("http://localhost:3000", "https://crm.example.com")


def test_parse_cors_origins_uses_local_defaults_for_empty_value() -> None:
    assert parse_cors_origins("") == DEFAULT_LOCAL_CORS_ORIGINS


def test_production_rejects_wildcard_cors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("API_CORS_ORIGINS", "*")

    with pytest.raises(ValueError, match="wildcard"):
        Settings.from_env()


def test_production_rejects_missing_or_unsafe_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("API_CORS_ORIGINS", "https://crm.example.com")
    monkeypatch.setenv("JWT_SECRET", "change-me")

    with pytest.raises(ValueError, match="JWT_SECRET"):
        Settings.from_env()


def test_production_forces_secure_auth_cookies(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("API_CORS_ORIGINS", "https://crm.example.com")
    monkeypatch.setenv("JWT_SECRET", "production-jwt-secret-with-enough-length")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")

    settings = Settings.from_env()

    assert settings.auth_cookie_secure is True


def test_database_url_is_required_for_database_operations() -> None:
    settings = Settings(app_env="test", api_cors_origins=("http://localhost:3000",))

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        settings.require_database_url()
