import asyncio
from datetime import date
import logging
from monitoring.push_monitoring import metrics

from sqlalchemy import func
from sqlalchemy.orm import Session
from telegram import Bot
from membership import fetch_boosty_patrons, fetch_patrons, membership

import models
import settings

logger = logging.getLogger("metrics_reporter")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()  # prints to stdout (captured by cron log)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def users_started_bot_count() -> int:
    with Session(models.engine) as session:
        users_count = session.query(models.User).count()
    logger.info(f"users_started_bot_count: {users_count}")
    return users_count


def users_failed_broadcast_count() -> int:
    with Session(models.engine) as session:
        failed_users_count = session.query(models.User).filter(models.User.is_last_message_successful.is_(False)).count()
    logger.info(f"users_failed_broadcast_count: {failed_users_count}")
    return failed_users_count


def set_activity_members() -> None:
    with Session(models.engine) as session:
        permanent_members = (
            session.query(func.count(models.MembershipByActivity.id))
            .filter(models.MembershipByActivity.expires_at.is_(None))
            .scalar()
        )

        temporary_members = (
            session.query(func.count(models.MembershipByActivity.id))
            .filter(models.MembershipByActivity.expires_at >= date.today())
            .scalar()
        )
    logger.info(f"permanent_activity_members: {permanent_members}")
    logger.info(f"temporary_activity_members: {temporary_members}")

    metrics.set(
        "activity_members",
        permanent_members,
        temporary="temporary"
    )
    metrics.set(
        "activity_members",
        temporary_members,
        temporary="permanent"
    )


def set_enrolled_users_map() -> None:
    with Session(models.engine) as session:
        results = (
            session.query(
                models.Course.name,
                func.count(models.Enrollment.id).label("enrolled_users")
            )
            .outerjoin(models.Enrollment, models.Course.id == models.Enrollment.course_id)
            .filter(models.Course.is_active.is_(True))
            .group_by(models.Course.name)
            .all()
        )

    course_map = {
        course_name: enrolled_users
        for course_name, enrolled_users in results
    }
    logger.info(f"{course_map=}")

    for course_name, enrolled_count in course_map.items():
        metrics.set(
            "enrolled_users",
            enrolled_count,
            course=course_name
        )


def set_enrolled_users_paid_map() -> None:
    with Session(models.engine) as session:
        results = (
            session.query(
                models.Course.name,
                models.Enrollment.tg_id,
            )
            .join(models.Course, models.Course.id == models.Enrollment.course_id)
            .filter(models.Course.is_active.is_(True))
            .all()
        )

    course_paid_map: dict[str, int] = {}

    for course_name, tg_id in results:
        membership_info = membership.get_user_membership_info(tg_id)

        if membership_info.get_patreon_level() == membership.pro or membership_info.get_boosty_level() == membership.pro:
            course_paid_map[course_name] = course_paid_map.get(course_name, 0) + 1

    logger.info(f"{course_paid_map=}")
    for course_name, enrolled_count in course_paid_map.items():
        metrics.set(
            "enrolled_paid_users",
            enrolled_count,
            course=course_name
        )


# todo: forgive me gods of performance and DRY
def set_enrolled_users_activity_membership_map() -> None:
    with Session(models.engine) as session:
        results = (
            session.query(
                models.Course.name,
                models.Enrollment.tg_id,
            )
            .join(models.Course, models.Course.id == models.Enrollment.course_id)
            .filter(models.Course.is_active.is_(True))
            .all()
        )

    course_activity_membership_map: dict[str, int] = {}

    for course_name, tg_id in results:
        membership_info = membership.get_user_membership_info(tg_id)
        if membership_info.get_activity_level() == membership.pro:
            course_activity_membership_map[course_name] = course_activity_membership_map.get(course_name, 0) + 1

    logger.info(f"{course_activity_membership_map=}")

    for course_name, enrolled_count in course_activity_membership_map.items():
        metrics.set(
            "enrolled_activity_membership_users",
            enrolled_count,
            course=course_name
        )


async def calculate_metrics_and_report(bot: Bot = None) -> None:
    logger.info("Starting metrics collection")
    try:
        metrics.set("users_started_bot", users_started_bot_count())
        metrics.set("users_failed_broadcast", users_failed_broadcast_count())
        metrics.set("patreon_patrons", len(fetch_patrons.get_patrons_from_redis("active_patron")))
        metrics.set("boosty_patrons", len(fetch_boosty_patrons.get_boosty_patrons_from_redis(1)))
        set_activity_members()

        set_enrolled_users_map()
        set_enrolled_users_paid_map()
        set_enrolled_users_activity_membership_map()

        metrics.push()
        logger.info("Metrics successfully pushed")
    except Exception as e:
        logger.error(f"Failed to collect or push metrics: {e}")
        if bot:
            await bot.send_message(
                chat_id=settings.ADMIN_CHAT_ID,
                text=f"Failed to collect or push metrics: {e}")


# this will be run periodically on cron
if __name__ == "__main__":
    asyncio.run(calculate_metrics_and_report())
