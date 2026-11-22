# Test conventions

- Keep fast, isolated tests in `unit/`; they should not require PostgreSQL or external services.
- Put tests that verify SQLAlchemy queries or database-backed behavior in `integration/` and use the `test_db` fixture.
- Under each layer, group test modules by feature area, such as `membership/` and `notifications/`.
- Integration tests require `TEST_DATABASE_URL` to point to the dedicated local `nelenkin_bot_test` database. Keep the safety checks in `integration/conftest.py`; never use a development or production database.
- Run database integration tests against the PostgreSQL `db` service in `docker-compose.yml`, using the dedicated `nelenkin_bot_test` database within that service. Do not add Testcontainers.
- Mock Telegram delivery, SMTP, Redis, and Patreon or Boosty lookups. Tests must not send real messages or contact live external services.
- Mark coroutine tests with `pytest.mark.asyncio`.
- Keep the entire `tests/` tree Ruff-clean; run `uv run ruff check tests` after test changes and fix all reported findings there.

For first-time integration test setup, create the dedicated database in the local
Docker PostgreSQL instance, then run the suite with:

```sh
docker compose up -d db
docker compose exec db createdb -U postgres nelenkin_bot_test
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nelenkin_bot_test uv run pytest
```
