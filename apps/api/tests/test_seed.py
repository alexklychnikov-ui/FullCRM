from os import environ

import pytest
from sqlalchemy import func, select

from app.db.models import Organization, Permission, Pipeline, PipelineStage, Role, User
from app.db.seed import seed_demo_data
from app.db.session import create_db_engine, create_session_factory


TEST_DATABASE_URL = environ.get("TEST_DATABASE_URL", "").strip()
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL is required for database seed integration tests",
)


def table_count(session_factory, model: type[object]) -> int:
    with session_factory() as session:
        return session.scalar(select(func.count()).select_from(model)) or 0


def demo_counts(session_factory) -> tuple[int, ...]:
    return tuple(
        table_count(session_factory, model)
        for model in (Organization, User, Role, Permission, Pipeline, PipelineStage)
    )


def test_seed_demo_data_is_idempotent() -> None:
    engine = create_db_engine(TEST_DATABASE_URL)
    session_factory = create_session_factory(engine)

    try:
        with session_factory() as session:
            seed_demo_data(session)

        first_counts = demo_counts(session_factory)

        with session_factory() as session:
            seed_demo_data(session)

        assert demo_counts(session_factory) == first_counts
    finally:
        engine.dispose()
