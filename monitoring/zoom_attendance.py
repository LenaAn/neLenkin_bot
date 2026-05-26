import base64
import logging
import os
from datetime import date, datetime

import requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session

import models
from monitoring.push_monitoring import MetricsPusher

logger = logging.getLogger("metrics_reporter")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()  # prints to stdout (captured by cron log)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


load_dotenv()

ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")
CLIENT_EMAIL = os.getenv("ZOOM_CLIENT_EMAIL")


def get_zoom_access_token():
    url = "https://zoom.us/oauth/token?grant_type=account_credentials&account_id=" + ACCOUNT_ID

    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}"
    }

    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()["access_token"]


def get_meeting_id_from_link(zoom_link: str) -> str:
    logger.info(f"extracting meeting id from {zoom_link}")
    items = zoom_link.split('/')
    params_str = items[4]
    params = params_str.split('?')

    logger.info(f"meeting id is {params[0]}")
    return params[0]


def get_participant_count(zoom_meeting_id: str) -> int | None:
    access_token = get_zoom_access_token()

    response = requests.get(
        f"https://api.zoom.us/v2/report/meetings/{zoom_meeting_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        timeout=30,
    )

    if response.status_code == 404:
        logger.info(f"No meeting found, returning None instead of participants_count")
        return None

    response.raise_for_status()
    data = response.json()
    logger.info(f"{data=}")

    participants_count = response.json()["participants_count"]
    logger.info(f"{participants_count=}")
    return participants_count


def set_zoom_attendance_for_active_courses(metrics_pusher: MetricsPusher) -> None:
    # in app.job_queue.run_daily 0 = Sunday, so in db 0 = Sunday, 1 = Monday
    # but for datetime 0 = Monday
    today_weekday: int = (datetime.now().weekday() + 1) % 7

    with Session(models.engine) as session:
        active_notifications_today = (
            session.query(
                models.Course,
                models.CourseNotification,
            )
            .join(models.Course, models.Course.id == models.CourseNotification.course_id)
            .filter((models.Course.is_active.is_(True)) & (models.CourseNotification.day_of_week == today_weekday))
            .all()
        )
        logger.info(f"{active_notifications_today=}")

        active_course_names_by_id = {
            course.id: course.name for course,  notification in active_notifications_today
        }
        logger.info(f"{active_course_names_by_id=}")

        scheduled_messages = (
            session.query(models.ScheduledPartMessages)
            .filter(
                models.ScheduledPartMessages.week_number == date.today().isocalendar().week,
                models.ScheduledPartMessages.course_id.in_(active_course_names_by_id),
            )
            .all()
        )
        logger.info(f"{scheduled_messages=}")

    for scheduled_msg in scheduled_messages:
        zoom_meeting_id = get_meeting_id_from_link(scheduled_msg.text)
        participant_count = get_participant_count(zoom_meeting_id)
        if participant_count:
            metrics_pusher.set(
                "zoom_attendance",
                participant_count,
                course=active_course_names_by_id[scheduled_msg.course_id]
            )
