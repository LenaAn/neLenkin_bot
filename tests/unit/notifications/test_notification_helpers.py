import os
from email.message import EmailMessage
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from notifications import notifications_helpers


@pytest.mark.asyncio
async def test_broadcast_sends_html_and_reports_to_admin(monkeypatch):
    monkeypatch.setattr(notifications_helpers, "load_dotenv", lambda **kwargs: None)
    update_users = AsyncMock()
    monkeypatch.setattr(
        notifications_helpers.update_users_in_db,
        "update_users_after_broadcast",
        update_users,
    )
    bot = SimpleNamespace(send_message=AsyncMock())

    await notifications_helpers.do_send_notifications(
        SimpleNamespace(bot=bot), ["101", "102"], "body", "menu", "weekly"
    )

    # Two recipient notifications plus one admin summary message.
    assert bot.send_message.await_count == 3
    assert bot.send_message.await_args_list[0].kwargs == {
        "chat_id": "101",
        "text": "body",
        "parse_mode": "HTML",
        "reply_markup": "menu",
    }
    update_users.assert_awaited_once()
    success, failures = update_users.await_args.args
    assert set(success) == {"101", "102"}
    assert failures == []
    assert bot.send_message.await_args_list[-1].kwargs["chat_id"] == int(os.environ["ADMIN_CHAT_ID"])


@pytest.mark.asyncio
async def test_broadcast_continues_after_send_error_and_records_failed_id(monkeypatch):
    monkeypatch.setattr(notifications_helpers, "load_dotenv", lambda **kwargs: None)
    update_users = AsyncMock()
    monkeypatch.setattr(
        notifications_helpers.update_users_in_db,
        "update_users_after_broadcast",
        update_users,
    )

    async def deliver(chat_id, **kwargs):
        if chat_id == "bad":
            raise RuntimeError("blocked")

    bot = SimpleNamespace(send_message=AsyncMock(side_effect=deliver))
    await notifications_helpers.do_send_notifications(
        SimpleNamespace(bot=bot), ["bad", "good"], "x", None, "n"
    )

    success, failures = update_users.await_args.args
    assert success == ["good"]
    assert failures == ["bad"]
    assert (
        "1 users, failed 1 users" in bot.send_message.await_args_list[-1].kwargs["text"]
    )


@pytest.mark.asyncio
async def test_send_emails_builds_bcc_message(monkeypatch):
    smtp_send = AsyncMock()
    monkeypatch.setattr(notifications_helpers.aiosmtplib, "send", smtp_send)

    await notifications_helpers.send_emails(
        "Subject", "Body", ["a@example.test", "b@example.test"]
    )

    message = smtp_send.await_args.args[0]
    assert isinstance(message, EmailMessage)
    assert message["Subject"] == "Subject"
    assert message["Bcc"] == "a@example.test, b@example.test"
    assert message.get_content().strip() == "Body"
    assert smtp_send.await_args.kwargs["start_tls"] is True
