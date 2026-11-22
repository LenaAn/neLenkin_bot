import datetime

import pytest
from sqlalchemy.orm import Session

import models
from notifications import notifications


@pytest.mark.asyncio
async def test_active_course_query_filters_by_day_hour_and_active_status(test_db):
    today = (datetime.datetime.now().weekday() + 1) % 7
    with Session(test_db) as session:
        session.add_all(
            [
                models.Course(id=42, name="Matching", is_active=True),
                models.Course(id=43, name="Inactive", is_active=False),
                models.Course(id=44, name="Other day", is_active=True),
                models.Course(id=45, name="Other hour", is_active=True),
            ]
        )
        session.add_all(
            [
                models.CourseNotification(
                    course_id=42,
                    is_zoom_link_only_to_pro=True,
                    send_patreon_reminder=False,
                    day_of_week=today,
                    hour=18,
                ),
                models.CourseNotification(
                    course_id=43,
                    is_zoom_link_only_to_pro=True,
                    send_patreon_reminder=False,
                    day_of_week=today,
                    hour=18,
                ),
                models.CourseNotification(
                    course_id=44,
                    is_zoom_link_only_to_pro=True,
                    send_patreon_reminder=False,
                    day_of_week=(today + 1) % 7,
                    hour=18,
                ),
                models.CourseNotification(
                    course_id=45,
                    is_zoom_link_only_to_pro=True,
                    send_patreon_reminder=False,
                    day_of_week=today,
                    hour=19,
                ),
            ]
        )
        session.commit()

    matches = notifications.get_active_courses_today(hour=18)

    assert [(course.id, notification.hour) for course, notification in matches] == [
        (42, 18)
    ]
