import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.orm import Session

import constants
import models
from notifications import notifications


@pytest.mark.asyncio
async def test_zoom_link_lookup_uses_current_iso_week_and_builds_reminder(
    test_db, monkeypatch
):
    course_id = 42
    course_name = "Test course"
    week_number = datetime.date.today().isocalendar().week
    call_link = "https://zoom.example.test/meeting"
    with Session(test_db) as session:
        session.add(
            models.Course(id=course_id, name=course_name, is_active=True, is_pro=True)
        )
        session.add(
            models.ScheduledPartMessages(
                course_id=course_id,
                week_number=week_number,
                text=call_link,
            )
        )
        session.commit()

    handle_zoom = AsyncMock()
    monkeypatch.setattr(notifications, "handle_send_zoom", handle_zoom)
    context = SimpleNamespace(job=SimpleNamespace(data={"course_id": course_id}))

    await notifications.get_zoom_link_and_send_for_course(context)

    assert context.job.data["message"] == (
        f"{constants.before_call_reminder.format(course_name)}\n\n{call_link}"
    )
    handle_zoom.assert_awaited_once_with(context)


@pytest.mark.asyncio
async def test_missing_zoom_link_notifies_admin_and_does_not_send(test_db, monkeypatch):
    monkeypatch.setenv("ADMIN_CHAT_ID", "999999999")
    monkeypatch.setattr(notifications, "load_dotenv", lambda **kwargs: None)
    handle_zoom = AsyncMock()
    monkeypatch.setattr(notifications, "handle_send_zoom", handle_zoom)
    bot = SimpleNamespace(send_message=AsyncMock())
    context = SimpleNamespace(job=SimpleNamespace(data={"course_id": 42}), bot=bot)

    with Session(test_db) as session:
        session.add(
            models.Course(id=42, name="Test course", is_active=True, is_pro=True)
        )
        session.commit()

    await notifications.get_zoom_link_and_send_for_course(context)

    bot.send_message.assert_awaited_once_with(
        chat_id=999999999,
        text="Zoom link for Test course not found for today!",
    )
    handle_zoom.assert_not_awaited()


@pytest.mark.asyncio
async def test_empty_zoom_link_still_sends_reminder_without_link(test_db, monkeypatch):
    course_id = 42
    course_name = "Test course"
    week_number = datetime.date.today().isocalendar().week
    with Session(test_db) as session:
        session.add(
            models.Course(id=course_id, name=course_name, is_active=True, is_pro=True)
        )
        session.add(
            models.ScheduledPartMessages(
                course_id=course_id, week_number=week_number, text=""
            )
        )
        session.commit()

    handle_zoom = AsyncMock()
    monkeypatch.setattr(notifications, "handle_send_zoom", handle_zoom)
    context = SimpleNamespace(job=SimpleNamespace(data={"course_id": course_id}))

    await notifications.get_zoom_link_and_send_for_course(context)

    assert context.job.data["message"] == constants.before_call_reminder.format(
        course_name
    )
    handle_zoom.assert_awaited_once_with(context)
