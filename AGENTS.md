# AGENTS.md

Guidance for coding agents working in this repository.

## Project overview

`neLenkin_bot` is a Python Telegram bot for the NeLenkin Club. It uses
`python-telegram-bot`, PostgreSQL with SQLAlchemy/Alembic, Redis, and external
membership and calendar services. `main.py` wires together bot handlers and
background jobs.

## Development commands

- Install dependencies (Python 3.14 or newer): `uv sync`
- Start local services: `docker compose up -d`
- Apply database migrations: `uv run alembic upgrade head`
- Run the bot: `uv run main.py`
- Run tests: `TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nelenkin_bot_test uv run pytest`
- Run Ruff on changed files: `uv run ruff check <changed files>`

`README.md` documents local setup and required environment variables.

## Working conventions

- Keep changes focused and follow the surrounding Python style. Avoid unrelated refactors.
- Run the full test suite with `uv run pytest` after every change. Set `TEST_DATABASE_URL` as documented above to include PostgreSQL integration tests.
- When a change affects guidance documented in this file, update the relevant instructions to keep them current.
- Preserve existing Telegram handler behavior and scheduled job registration when changing bot flows.
- When changing the database schema, generate an Alembic migration with `uv run alembic revision --autogenerate -m <message>` and keep it consistent with `models.py`. Do not modify generated files by hand or rewrite already-applied migrations.
- Treat membership/payment integrations and bulk messaging as production-sensitive; avoid triggering external actions while developing or checking changes.
- Do not overwrite unrelated working-tree changes. In particular, inspect existing changes before editing files they touch.
- Never commit unless asked. Make git commits, merges, and pushes only when the user explicitly requests them. Otherwise leave changes in the working tree — staging and committing are user-initiated.

## Verification

Before calling work finished, run:

1. The full test suite with `TEST_DATABASE_URL` set to the dedicated local
   `nelenkin_bot_test` database, as shown above.
2. Ruff on files changed for the task. Fix findings introduced by the changes;
   leave pre-existing Ruff findings untouched.

If a command fails, fix issues introduced by the task and rerun it.
