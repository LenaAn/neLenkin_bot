from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from notifications import notifications


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("hour", "courses"),
    [
        (18, [(42, True), (43, False)]),
        (19, [(44, False), (45, True)]),
    ],
)
async def test_scheduled_job_dispatches_courses_for_each_notification_hour(
    monkeypatch, hour, courses
):
    active_courses = [
        (
            SimpleNamespace(id=course_id),
            SimpleNamespace(is_zoom_link_only_to_pro=pro_only),
        )
        for course_id, pro_only in courses
    ]
    get_active_courses = Mock(return_value=active_courses)
    monkeypatch.setattr(notifications, "get_active_courses_today", get_active_courses)
    dispatched_data = []

    async def capture_dispatch(context):
        # The job reuses and mutates its data for each course; snapshot each dispatch.
        dispatched_data.append(context.job.data.copy())

    send_for_course = AsyncMock(side_effect=capture_dispatch)
    monkeypatch.setattr(
        notifications, "get_zoom_link_and_send_for_course", send_for_course
    )
    context = SimpleNamespace(job=SimpleNamespace(data={"hour": hour}))

    await notifications.get_active_courses_and_send_zoom(context)

    get_active_courses.assert_called_once_with(hour)
    assert dispatched_data == [
        {"hour": hour, "course_id": course_id, "is_zoom_link_only_to_pro": pro_only}
        for course_id, pro_only in courses
    ]
    assert send_for_course.await_count == len(courses)
    assert all(call.args[0] is context for call in send_for_course.await_args_list)
