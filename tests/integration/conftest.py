from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from alembic import command


@pytest.fixture(scope="session")
def test_engine():
    import os

    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL integration tests")

    url = make_url(database_url)
    if url.database != "nelenkin_bot_test" or url.host not in {
        "localhost",
        "127.0.0.1",
        "::1",
    }:
        pytest.fail(
            "Refusing to run database tests unless TEST_DATABASE_URL points to "
            "nelenkin_bot_test on localhost"
        )

    engine = create_engine(database_url)
    alembic_config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    alembic_config.set_main_option(
        "sqlalchemy.url",
        url.render_as_string(hide_password=False).replace("%", "%%"),
    )
    command.upgrade(alembic_config, "head")

    yield engine
    engine.dispose()


@pytest.fixture
def test_db(test_engine, monkeypatch):
    import models
    from notifications import notifications

    monkeypatch.setattr(models, "engine", test_engine)
    monkeypatch.setattr(notifications, "engine", test_engine)

    def clear_tables():
        with test_engine.begin() as connection:
            tables = ", ".join(
                connection.dialect.identifier_preparer.quote(table.name)
                for table in models.Base.metadata.sorted_tables
            )
            connection.exec_driver_sql(
                f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"
            )

    clear_tables()
    yield test_engine
    clear_tables()
