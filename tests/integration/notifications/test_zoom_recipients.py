from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.orm import Session

import models
from membership import membership
from notifications import notifications


@pytest.mark.parametrize(
    ("course_is_pro", "only_pro", "expected_ids"),
    [
        (True, True, {"101"}),
        (True, False, {"101", "102"}),
        (False, True, {"101"}),
        (False, False, {"101", "102"}),
    ],
)
@pytest.mark.asyncio
async def test_zoom_reminder_targets_enrolled_members_and_respects_notification_flag(
    test_db, monkeypatch, course_is_pro, only_pro, expected_ids
):
    with Session(test_db) as session:
        session.add_all(
            [
                models.Course(
                    id=42, name="Test course", is_active=True, is_pro=course_is_pro
                ),
                models.User(tg_id="101"),
                models.User(tg_id="102"),
                models.User(tg_id="103"),
                models.Enrollment(course_id=42, tg_id="101"),
                models.Enrollment(course_id=42, tg_id="102"),
            ]
        )
        session.commit()

    levels = {"101": membership.pro, "102": membership.basic}
    membership_lookup = Mock(
        side_effect=lambda tg_id: SimpleNamespace(
            get_overall_level=lambda: levels[tg_id]
        )
    )
    monkeypatch.setattr(
        notifications.membership, "get_user_membership_info", membership_lookup
    )
    send_notifications = AsyncMock()
    send_emails = AsyncMock()
    monkeypatch.setattr(
        notifications.notifications_helpers, "do_send_notifications", send_notifications
    )
    monkeypatch.setattr(
        notifications.notifications_helpers, "email_notifications", send_emails
    )

    context = SimpleNamespace(
        job=SimpleNamespace(
            data={
                "course_id": 42,
                "is_zoom_link_only_to_pro": only_pro,
                "message": "Zoom link",
            }
        ),
        bot=AsyncMock(),
    )
    await notifications.handle_send_zoom(context)

    actual_ids = send_notifications.await_args.args[1]
    assert set(actual_ids) == expected_ids
    assert send_notifications.await_args.args[2] == "Zoom link"
    assert send_notifications.await_args.args[4] == "Test course"
    assert send_emails.await_args.args[1] == actual_ids
    if only_pro:
        assert set(actual_ids) <= set(levels)
        assert {call.args[0] for call in membership_lookup.call_args_list} == set(
            levels
        )
    else:
        assert set(actual_ids) == {"101", "102"}
        membership_lookup.assert_not_called()
