# AGENTS.md

Guidance for coding agents working in this repository.

## Project overview

`neLenkin_bot` is a Python Telegram bot for the NeLenkin Club. It uses
`python-telegram-bot`, PostgreSQL with SQLAlchemy/Alembic, Redis, and external
membership and calendar services. `main.py` wires together bot handlers and
background jobs.

## Development commands

The project uses `uv` and requires Python 3.14 or newer.

```sh
uv sync
docker compose up -d
alembic upgrade head
uv run main.py
```

`README.md` has the local setup steps and required environment variables. There
is no configured automated test or lint command in the repository; use focused
manual checks when appropriate and report what was verified.

## Working conventions

- Keep changes focused and follow the surrounding Python style. Avoid unrelated refactors.
- When a change affects guidance documented in this file, update the relevant instructions to keep them current.
- Preserve existing Telegram handler behavior and scheduled job registration when changing bot flows.
- When changing the database schema, generate an Alembic migration with `uv run alembic revision --autogenerate -m <message>` and keep it consistent with `models.py`. Do not modify generated files by hand or rewrite already-applied migrations.
- Treat membership/payment integrations and bulk messaging as production-sensitive; avoid triggering external actions while developing or checking changes.
- Do not overwrite unrelated working-tree changes. In particular, inspect existing changes before editing files they touch.
- Never commit unless asked. Make git commits, merges, and pushes only when the user explicitly requests them. Otherwise leave changes in the working tree — staging and committing are user-initiated.
