from dataclasses import dataclass
from os import getenv


DEFAULT_LOCAL_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)
UNSAFE_JWT_SECRETS = frozenset(
    {
        "change-me",
        "changeme",
        "secret",
        "dev-secret",
        "fullcrm-secret",
        "please-change-me",
    }
)


@dataclass(frozen=True)
class Settings:
    app_env: str
    api_cors_origins: tuple[str, ...]
    database_url: str | None = None
    jwt_secret: str | None = None
    jwt_access_ttl_seconds: int = 15 * 60
    jwt_refresh_ttl_seconds: int = 7 * 24 * 60 * 60
    auth_access_cookie_name: str = "fullcrm_access"
    auth_refresh_cookie_name: str = "fullcrm_refresh"
    auth_cookie_samesite: str = "lax"
    auth_cookie_secure: bool = False
    service_name: str = "fullcrm-api"
    telegram_bot_token: str | None = None
    telegram_enabled: bool = False
    telegram_poll_cooldown_seconds: int = 30
    openai_api_key: str | None = None
    ai_mock: bool = True
    ai_model: str = "gpt-4o-mini"

    @classmethod
    def from_env(cls) -> "Settings":
        app_env = getenv("APP_ENV", "local").strip().lower() or "local"
        origins = parse_cors_origins(getenv("API_CORS_ORIGINS"))

        if app_env == "production" and "*" in origins:
            raise ValueError("API_CORS_ORIGINS must not contain wildcard in production")

        database_url = getenv("DATABASE_URL")
        jwt_secret = clean_env("JWT_SECRET")

        if app_env == "production" and not is_safe_jwt_secret(jwt_secret):
            raise ValueError("JWT_SECRET must be set to a strong value in production")

        return cls(
            app_env=app_env,
            api_cors_origins=origins,
            database_url=database_url.strip() if database_url else None,
            jwt_secret=jwt_secret,
            jwt_access_ttl_seconds=parse_positive_int("JWT_ACCESS_TTL_SECONDS", 15 * 60),
            jwt_refresh_ttl_seconds=parse_positive_int("JWT_REFRESH_TTL_SECONDS", 7 * 24 * 60 * 60),
            auth_access_cookie_name=clean_env("AUTH_ACCESS_COOKIE_NAME") or "fullcrm_access",
            auth_refresh_cookie_name=clean_env("AUTH_REFRESH_COOKIE_NAME") or "fullcrm_refresh",
            auth_cookie_samesite=(clean_env("AUTH_COOKIE_SAMESITE") or "lax").lower(),
            auth_cookie_secure=app_env == "production" or parse_bool_env("AUTH_COOKIE_SECURE", False),
            telegram_bot_token=clean_env("TELEGRAM_BOT_TOKEN"),
            telegram_enabled=parse_bool_env("TELEGRAM_ENABLED", False),
            telegram_poll_cooldown_seconds=parse_positive_int("TELEGRAM_POLL_COOLDOWN_SECONDS", 30),
            openai_api_key=clean_env("OPENAI_API_KEY"),
            ai_mock=parse_bool_env("AI_MOCK", True),
            ai_model=resolve_ai_model_from_env(),
        )

    def require_database_url(self) -> str:
        if not self.database_url:
            raise RuntimeError("DATABASE_URL must be set for database operations")

        return self.database_url

    def require_jwt_secret(self) -> str:
        if not self.jwt_secret:
            raise RuntimeError("JWT_SECRET must be set for auth operations")

        return self.jwt_secret

    @property
    def auth_cookie_max_age_seconds(self) -> int:
        return self.jwt_refresh_ttl_seconds


def parse_cors_origins(raw_origins: str | None) -> tuple[str, ...]:
    if raw_origins is None or raw_origins.strip() == "":
        return DEFAULT_LOCAL_CORS_ORIGINS

    origins = tuple(
        origin.strip()
        for origin in raw_origins.split(",")
        if origin.strip()
    )
    return origins or DEFAULT_LOCAL_CORS_ORIGINS


def clean_env(name: str) -> str | None:
    value = getenv(name)

    if value is None:
        return None

    stripped = value.strip()
    return stripped or None


def parse_positive_int(name: str, default: int) -> int:
    raw_value = clean_env(name)

    if raw_value is None:
        return default

    value = int(raw_value)

    if value <= 0:
        raise ValueError(f"{name} must be positive")

    return value


def parse_bool_env(name: str, default: bool) -> bool:
    raw_value = clean_env(name)

    if raw_value is None:
        return default

    return raw_value.lower() in {"1", "true", "yes", "on"}


def resolve_ai_model_from_env(default: str = "gpt-4o-mini") -> str:
    return clean_env("AI_MODEL") or clean_env("OPENAI_MODEL") or default


def is_safe_jwt_secret(secret: str | None) -> bool:
    if secret is None:
        return False

    normalized = secret.strip().lower()
    return len(secret) >= 32 and normalized not in UNSAFE_JWT_SECRETS
