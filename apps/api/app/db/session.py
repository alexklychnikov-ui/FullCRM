from collections.abc import Generator
from threading import RLock

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings


_cache_lock = RLock()
_engine_cache: dict[str, Engine] = {}
_session_factory_cache: dict[str, sessionmaker[Session]] = {}


def resolve_database_url(database_url: str | None = None) -> str:
    return database_url or Settings.from_env().require_database_url()


def create_db_engine(database_url: str | None = None) -> Engine:
    resolved_url = resolve_database_url(database_url)
    return create_engine(resolved_url, pool_pre_ping=True)


def create_session_factory(
    engine: Engine | None = None,
    database_url: str | None = None,
) -> sessionmaker[Session]:
    if engine is not None:
        return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    return get_session_factory(database_url)


def get_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    resolved_url = resolve_database_url(database_url)

    with _cache_lock:
        cached_factory = _session_factory_cache.get(resolved_url)

        if cached_factory is not None:
            return cached_factory

        engine = _engine_cache.get(resolved_url)

        if engine is None:
            engine = create_db_engine(resolved_url)
            _engine_cache[resolved_url] = engine

        session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        _session_factory_cache[resolved_url] = session_factory
        return session_factory


def clear_session_cache(dispose: bool = True) -> None:
    with _cache_lock:
        engines = tuple(_engine_cache.values())
        _engine_cache.clear()
        _session_factory_cache.clear()

    if dispose:
        for engine in engines:
            engine.dispose()


SessionLocal = create_session_factory


def get_db_session() -> Generator[Session]:
    session_factory = get_session_factory()

    with session_factory() as session:
        yield session
