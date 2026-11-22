import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.orm import Session

import constants
import models
from membership import membership
from notifications import notifications


@pytest.mark.asyncio
async def test_prompt_targets_only_basic_enrolled_members(test_db, monkeypatch):
    with Session(test_db) as session:
        session.add(
            models.Course(id=42, name="Test course", is_active=True, is_pro=True)
        )
        session.add_all([models.User(tg_id=str(i)) for i in (101, 102, 103)])
        session.add_all(
            [models.Enrollment(course_id=42, tg_id=str(i)) for i in (101, 102, 103)]
        )
        session.commit()
    levels = {"101": membership.basic, "102": membership.pro, "103": membership.basic}
    lookup = Mock(
        side_effect=lambda tg_id: SimpleNamespace(
            get_overall_level=lambda: levels[tg_id]
        )
    )
    monkeypatch.setattr(notifications.membership, "get_user_membership_info", lookup)
    send = AsyncMock()
    monkeypatch.setattr(
        notifications.notifications_helpers, "do_send_notifications", send
    )

    await notifications.prompt_to_connect_patreon_notifications(
        SimpleNamespace(job=SimpleNamespace(data={"course_id": 42}))
    )

    assert send.await_args.args[1] == ["101", "103"]
    assert "Test course" in send.await_args.args[2]
    assert send.await_args.args[3].inline_keyboard[-1][0].callback_data == "unenroll:42"


@pytest.mark.asyncio
async def test_prompt_sends_empty_list_when_all_enrolled_members_are_pro(
    test_db, monkeypatch
):
    with Session(test_db) as session:
        session.add(
            models.Course(id=42, name="Test course", is_active=True, is_pro=True)
        )
        session.add(models.User(tg_id="101"))
        session.add(models.Enrollment(course_id=42, tg_id="101"))
        session.commit()
    monkeypatch.setattr(
        notifications.membership,
        "get_user_membership_info",
        lambda _: SimpleNamespace(get_overall_level=lambda: membership.pro),
    )
    send = AsyncMock()
    monkeypatch.setattr(
        notifications.notifications_helpers, "do_send_notifications", send
    )

    await notifications.prompt_to_connect_patreon_notifications(
        SimpleNamespace(job=SimpleNamespace(data={"course_id": 42}))
    )

    assert send.await_args.args[1] == []


@pytest.mark.asyncio
async def test_leetcode_reminder_skips_members_signed_up_this_week(
    test_db, monkeypatch
):
    week = datetime.date.today().isocalendar().week
    with Session(test_db) as session:
        session.add(
            models.Course(
                id=constants.leetcode_course_id, name="Leetcode", is_active=True
            )
        )
        session.add_all([models.User(tg_id="101"), models.User(tg_id="102")])
        session.add_all(
            [
                models.Enrollment(course_id=constants.leetcode_course_id, tg_id="101"),
                models.Enrollment(course_id=constants.leetcode_course_id, tg_id="102"),
                models.MockSignUp(
                    week_number=week,
                    tg_id="102",
                    tg_username="u",
                    first_problem="a",
                    second_problem="b",
                    selected_timeslots=[],
                    programming_language="Python",
                ),
                models.ScheduledPartMessages(
                    week_number=week,
                    course_id=constants.leetcode_course_id,
                    text="Topic",
                ),
            ]
        )
        session.commit()
    send = AsyncMock()
    monkeypatch.setattr(
        notifications.notifications_helpers, "do_send_notifications", send
    )

    await notifications.handle_leetcode_reminder(SimpleNamespace(bot=AsyncMock()))

    assert send.await_args.args[1] == ["101"]
    assert send.await_args.args[4] == "Leetcode"


@pytest.mark.asyncio
async def test_missing_leetcode_topic_alerts_admin_without_broadcast(
    test_db, monkeypatch
):
    send = AsyncMock()
    monkeypatch.setattr(
        notifications.notifications_helpers, "do_send_notifications", send
    )
    bot = SimpleNamespace(send_message=AsyncMock())

    await notifications.handle_leetcode_reminder(SimpleNamespace(bot=bot))

    send.assert_not_awaited()
    bot.send_message.assert_awaited_once()
    assert "No leetcode topic" in bot.send_message.await_args.kwargs["text"]


@pytest.mark.asyncio
async def test_aoc_notification_respects_toggle(monkeypatch):
    bot = SimpleNamespace(send_message=AsyncMock())
    monkeypatch.setattr(models, "aoc_notification_on", False)
    await notifications.handle_aoc_notification(SimpleNamespace(bot=bot))
    bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_active_course_prompt_job_skips_disabled_prompts(monkeypatch):
    course = SimpleNamespace(id=42, name="Test")
    enabled = SimpleNamespace(send_patreon_reminder=True)
    disabled = SimpleNamespace(send_patreon_reminder=False)
    monkeypatch.setattr(
        notifications,
        "get_active_courses_today",
        lambda: [(course, enabled), (course, disabled)],
    )
    prompt = AsyncMock()
    monkeypatch.setattr(
        notifications, "prompt_to_connect_patreon_notifications", prompt
    )
    context = SimpleNamespace(job=SimpleNamespace(data={"old": True}))

    await notifications.get_active_courses_and_prompt_to_get_pro(context)

    prompt.assert_awaited_once_with(context)
    assert context.job.data == {"course_id": 42}
