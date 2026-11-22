from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.orm import Session

import models
from notifications import notifications_helpers


@pytest.mark.asyncio
async def test_telegram_delivery_records_successes_and_failures(test_db, monkeypatch):
    monkeypatch.setattr(notifications_helpers, "load_dotenv", lambda **kwargs: None)
    with Session(test_db) as session:
        session.add_all([models.User(tg_id="101"), models.User(tg_id="102")])
        session.commit()

    async def send_message(chat_id, **kwargs):
        if chat_id == "102":
            raise RuntimeError("Telegram send failed")

    context = SimpleNamespace(
        bot=SimpleNamespace(send_message=AsyncMock(side_effect=send_message))
    )

    await notifications_helpers.do_send_notifications(
        context,
        ["101", "102"],
        "Zoom link",
        None,
        "Test course",
    )

    assert context.bot.send_message.await_count == 3
    assert context.bot.send_message.await_args_list[-1].kwargs["text"] == (
        "Successfully sent Test course notifications to 1 users, failed 1 users."
    )
    with Session(test_db) as session:
        users = {user.tg_id: user for user in session.query(models.User).all()}
    assert users["101"].is_last_message_successful is True
    assert users["101"].last_message_try_time is not None
    assert users["102"].is_last_message_successful is False
    assert users["102"].last_message_try_time is not None


@pytest.mark.asyncio
async def test_emails_are_sent_only_to_selected_recipients(test_db, monkeypatch):
    send_emails = AsyncMock()
    monkeypatch.setattr(notifications_helpers, "send_emails", send_emails)
    with Session(test_db) as session:
        session.add_all([models.User(tg_id="101"), models.User(tg_id="102")])
        session.flush()
        session.add_all(
            [
                models.UserEmail(tg_id="101", contact_email="selected@example.test"),
                models.UserEmail(
                    tg_id="102", contact_email="not-selected@example.test"
                ),
            ]
        )
        session.commit()

    context = SimpleNamespace(bot=SimpleNamespace(send_message=AsyncMock()))
    await notifications_helpers.email_notifications(
        context,
        ["101"],
        "Zoom link",
        None,
        "Test course",
    )

    send_emails.assert_awaited_once_with(
        subject="Звонок Test course через 5 минут!",
        body="Zoom link",
        recipients=["selected@example.test"],
    )
    context.bot.send_message.assert_awaited_once()
    assert (
        context.bot.send_message.await_args.kwargs["text"]
        == "Sent Test course notification to 1 emails"
    )


@pytest.mark.asyncio
async def test_email_notifications_skips_smtp_when_no_recipients(test_db, monkeypatch):
    send_emails = AsyncMock()
    monkeypatch.setattr(notifications_helpers, "send_emails", send_emails)
    bot = SimpleNamespace(send_message=AsyncMock())

    await notifications_helpers.email_notifications(
        SimpleNamespace(bot=bot), [], "body", None, "course"
    )

    send_emails.assert_not_awaited()
    assert "0 emails" in bot.send_message.await_args.kwargs["text"]
