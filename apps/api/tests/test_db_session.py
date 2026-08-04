from sqlalchemy import create_engine

from app.db.session import clear_session_cache, create_session_factory, get_session_factory


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
