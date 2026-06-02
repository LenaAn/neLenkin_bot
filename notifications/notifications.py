import datetime
import logging
import os
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import constants
from courses import course_handlers
import models
from models import Enrollment, ScheduledPartMessages, engine
from membership import membership
import settings
from . import notifications_helpers

notifications_logger = logging.getLogger(__name__)
notifications_logger.setLevel(logging.DEBUG)


async def register_notifications(application):
    await register_leetcode_notifications(application)
    await register_daily_send_zoom_for_active_courses(application)
    await register_daily_patreon_prompt_for_active_courses(application)
    await register_aoc_notifications(application)


async def handle_leetcode_reminder(context: ContextTypes.DEFAULT_TYPE):
    course_id: int = context.job.data["course_id"]
    if "message" not in context.job.data:
        admin_chat_id = int(os.getenv('ADMIN_CHAT_ID'))
        notifications_logger.error(
            f"Can't handle notification, there's no message in context.job.data: {context.job.data}")
        await context.bot.send_message(
            chat_id=admin_chat_id,
            text=f"Can't handle notification, there's no message in context.job.data: {context.job.data}"
        )
        return

    message: str = context.job.data["message"]
    menu: InlineKeyboardMarkup = context.job.data["menu"] if "menu" in context.job.data else None
    with Session(engine) as session:
        subquery = (
            select(models.MockSignUp.tg_id)
            .where(models.MockSignUp.week_number == datetime.date.today().isocalendar().week)
        )

        result = (
            session.query(Enrollment.tg_id)
            .filter(Enrollment.course_id == course_id)
            .filter(~Enrollment.tg_id.in_(subquery))
            .all()
        )

    notification_chat_ids = [item[0] for item in result]
    notifications_logger.debug(f"handling {constants.id_to_course[course_id]} notification, "
                               f"got {len(notification_chat_ids)} chat ids that are enrolled to Leetcode and not signed "
                               f"for this week")

    await notifications_helpers.do_send_notifications(context, notification_chat_ids, message, menu,
                                                      constants.id_to_course[course_id])


async def handle_send_zoom(context: ContextTypes.DEFAULT_TYPE):
    course_id: int = context.job.data["course_id"]
    is_zoom_link_only_to_pro: bool = context.job.data["is_zoom_link_only_to_pro"]

    if "message" not in context.job.data:
        admin_chat_id = int(os.getenv('ADMIN_CHAT_ID'))
        notifications_logger.error(
            f"Can't handle notification, there's no message in context.job.data: {context.job.data}")
        await context.bot.send_message(
            chat_id=admin_chat_id,
            text=f"Can't handle notification, there's no message in context.job.data: {context.job.data}"
        )
        return

    message: str = context.job.data["message"]
    menu: InlineKeyboardMarkup = context.job.data["menu"] if "menu" in context.job.data else None
    with Session(engine) as session:
        result = session.query(Enrollment.tg_id).filter(Enrollment.course_id == course_id).all()
        notification_chat_ids = [item[0] for item in result]
    notifications_logger.debug(f"handling {constants.id_to_course[course_id]} notification, "
                               f"got {len(notification_chat_ids)} chat ids that are subscribed to the course")

    if is_zoom_link_only_to_pro:
        notification_chat_ids = [tg_id for tg_id in notification_chat_ids
                                 if membership.get_user_membership_info(tg_id).get_overall_level() == membership.pro]
        notifications_logger.debug(f"handling {constants.id_to_course[course_id]} notification, "
                                   f"got {len(notification_chat_ids)} PRO subscribers")
    else:
        notifications_logger.debug(f"Sending a link to everyone because is_zoom_link_only_to_pro for {course_id} is False")

    await notifications_helpers.do_send_notifications(context, notification_chat_ids, message, menu,
                                                      constants.id_to_course[course_id])
    await notifications_helpers.email_notifications(context, notification_chat_ids, message, menu,
                                                    constants.id_to_course[course_id])


async def handle_aoc_notification(context: ContextTypes.DEFAULT_TYPE):
    if models.aoc_notification_on:
        from aoc import fetch_leaderboard
        notifications_logger.debug("Sending an AoC update to the main chat's AoC thread")
        formatted_report = fetch_leaderboard.get_formatted_leaderboard()
        await context.bot.send_message(
            chat_id=settings.CLUB_GROUP_CHAT_ID,
            message_thread_id=settings.AOC_TOPIC_ID,
            text=formatted_report,
            parse_mode="HTML",
        )
        notifications_logger.info("Successfully sent AoC leaderboard update")
    else:
        notifications_logger.info("AoC notification is turned off, skipping sending notifications")


async def get_zoom_link_and_send_for_course(context: ContextTypes.DEFAULT_TYPE):
    course_id: int = context.job.data["course_id"]
    current_week: int = datetime.date.today().isocalendar().week
    with (Session(engine) as session):
        try:
            call_link = session.query(ScheduledPartMessages.text) \
                .filter(
                    (ScheduledPartMessages.course_id == course_id) &
                    (ScheduledPartMessages.week_number == current_week)) \
                .one()[0]
        except NoResultFound as e:
            load_dotenv(override=True)
            admin_chat_id = int(os.getenv('ADMIN_CHAT_ID'))
            notifications_logger.debug(f"reloaded admin chat id: {admin_chat_id}")

            await context.bot.send_message(
                chat_id=admin_chat_id,
                text=f"Zoom link for {constants.id_to_course[course_id]} not found for today!"
            )
            notifications_logger.error('Zoom link for {constants.id_to_course[course_id]} not found for today!',
                                       exc_info=e)
            return

        notifications_logger.info(f'call_link is {call_link}')

    if call_link:
        context.job.data["message"] = \
            f"{constants.before_call_reminder.format(constants.id_to_course[course_id])}\n\n{call_link}"
    else:
        context.job.data["message"] = constants.before_call_reminder.format(constants.id_to_course[course_id])
    await handle_send_zoom(context)


async def prompt_to_connect_patreon_notifications(context: ContextTypes.DEFAULT_TYPE):
    course_id: int = context.job.data["course_id"]
    notifications_logger.info(f"prompt_to_connect_patreon_notifications for {constants.id_to_course[course_id]}")

    message: str = (f"Привет! Сегодня вечером будет звонок с обсуждением {constants.id_to_course[course_id]}."
                    f"\n\n<b>{constants.id_to_course[course_id]} — это 💜Pro курс, и чтобы сегодня вечером тебе пришла"
                    f" ссылка на звонок, нужна 💜Pro подписка!</b>"
                    f"\n\n1. Чтобы оформить Pro подписку, подпишись на донат в $15 в месяц на моем "
                    f"<a href='https://www.patreon.com/c/LenaAnyusha'>Patreon</a>."
                    f"\nКогда оформишь подписку на Patreon, привяжи почту по кнопке ⬇️"
                    f"\n\n2. Либо оформи подписку на 1500 рублей на мой <a href='https://boosty.to/lenaan'>Boosty</a> и "
                    f"привяжи почту по кнопке ⬇️"
                    f"\n\n3. Если возникнут какие-то сложности, напиши @lenka_colenka!"
                    f"\n\n4. Ты можешь отписаться от новостей про {constants.id_to_course[course_id]}, чтобы больше не "
                    f"получать уведомления.")
    menu = InlineKeyboardMarkup([
        [InlineKeyboardButton("Привязать профиль Patreon", callback_data="connect_patreon")],
        [InlineKeyboardButton("Привязать профиль Boosty", callback_data="connect_boosty")],
        [InlineKeyboardButton(f"Перестать получать уведомления о {constants.id_to_course[course_id]}",
                              callback_data=f"unenroll:{course_id}")],
    ])

    with Session(engine) as session:
        result = session.query(Enrollment.tg_id).filter(Enrollment.course_id == course_id).all()
        notification_chat_ids = [item[0] for item in result]
    notifications_logger.info(f"handling Patreon prompt for {constants.id_to_course[course_id]}, got "
                              f"{len(notification_chat_ids)} chat ids that are subscribed to the course")

    # only Basic subscribers will get a prompt to subscribe to Patreon
    notification_chat_ids = [tg_id for tg_id in notification_chat_ids
                             if membership.get_user_membership_info(tg_id).get_overall_level() == membership.basic]
    notifications_logger.info(f"handling Patreon prompt for {constants.id_to_course[course_id]}, got "
                              f"{len(notification_chat_ids)} Basic subscribers to {constants.id_to_course[course_id]}")

    await notifications_helpers.do_send_notifications(context, notification_chat_ids, message, menu,
                                                      f"{constants.id_to_course[course_id]} Patreon prompt")

# no matter winter or summer time in Europe.
# In theory should work without restart when the time changes
berlin_tz = ZoneInfo("Europe/Berlin")


async def register_leetcode_notifications(app):
    app.job_queue.run_daily(
        callback=handle_leetcode_reminder,
        time=datetime.time(hour=17, minute=6, tzinfo=berlin_tz),
        days=(4,),  # 0 = Sunday, ..., 4 = Thursday
        name=f"leetcode_mocks_reminder",
        data={
            "course_id": constants.leetcode_course_id,
            "message": constants.mock_leetcode_reminder,
            "menu": InlineKeyboardMarkup(
                [[InlineKeyboardButton("Записаться на моки!", callback_data="leetcode_register")]])
        }
    )


async def register_aoc_notifications(app):
    # should not hit API more than once every 15 minutes. Daily is fine
    app.job_queue.run_daily(
        callback=handle_aoc_notification,
        time=datetime.time(hour=20, minute=20, tzinfo=berlin_tz),
        days=(0, 1, 2, 3, 4, 5, 6),  # 0 = Sunday
        name=f"aoc_notification",
        data={"course_id": constants.aoc_course_id}
    )


def get_active_courses_today(hour: int = None) -> list[tuple[models.Course, models.CourseNotification]]:
    # in app.job_queue.run_daily 0 = Sunday, so in db 0 = Sunday, 1 = Monday
    # but for datetime 0 = Monday
    today_weekday: int = (datetime.datetime.now().weekday() + 1) % 7

    with Session(models.engine) as session:
        query = session.query(models.Course, models.CourseNotification
                              ).join(models.CourseNotification, models.Course.id == models.CourseNotification.course_id
                                     ).filter(
            (models.Course.is_active.is_(True) & (models.CourseNotification.day_of_week == today_weekday))
        )

        if hour is not None:
            query = query.filter(models.CourseNotification.hour == hour)
        active_courses_with_notification_today = query.all()

    notifications_logger.info(f"active courses for weekday {today_weekday} with hour {hour} are: "
                              f"{active_courses_with_notification_today}")
    return active_courses_with_notification_today


async def get_active_courses_and_send_zoom(context: ContextTypes.DEFAULT_TYPE):
    notifications_logger.info(f"triggered get_active_courses_and_send_zoom")

    active_courses_today: list[tuple[models.Course, models.CourseNotification]] = (
        get_active_courses_today(context.job.data["hour"]))
    for course, notification in active_courses_today:
        context.job.data["course_id"] = course.id
        context.job.data["is_zoom_link_only_to_pro"] = notification.is_zoom_link_only_to_pro
        await get_zoom_link_and_send_for_course(context)


async def get_active_courses_and_prompt_to_get_pro(context: ContextTypes.DEFAULT_TYPE):
    notifications_logger.info(f"triggered get_active_courses_and_prompt_to_get_pro")

    active_courses_today: list[tuple[models.Course, models.CourseNotification]] = get_active_courses_today()
    for course, notification in active_courses_today:
        if notification.send_patreon_reminder:
            context.job.data = {"course_id": course.id}
            await prompt_to_connect_patreon_notifications(context)
        else:
            notifications_logger.info(f"skipping patreon prompt for {course} since send_patreon_reminder is False")


# every day the job checks for active courses with today's day of the week
# and send a notification at 17:53 Berlin time.
# No need to restart when changing the set of active courses
async def register_daily_send_zoom_for_active_courses(app):
    app.job_queue.run_daily(
        callback=get_active_courses_and_send_zoom,
        time=datetime.time(hour=17, minute=53, tzinfo=berlin_tz),
        name=f"get_active_courses_and_send_zoom_1753",
        data={
            "hour": 18,
        }
    )
    app.job_queue.run_daily(
        callback=get_active_courses_and_send_zoom,
        time=datetime.time(hour=18, minute=53, tzinfo=berlin_tz),
        name=f"get_active_courses_and_send_zoom_1853",
        data={
            "hour": 19,
        }
    )


# every morning the job checks for active courses with today's day of the week
# and send a prompt to get Pro at 9:55 Berlin time.
# No need to restart when changing the set of active courses
async def register_daily_patreon_prompt_for_active_courses(app):
    app.job_queue.run_daily(
        callback=get_active_courses_and_prompt_to_get_pro,
        time=datetime.time(hour=9, minute=55, tzinfo=berlin_tz),
        name=f"get_active_course_and_prompt_to_get_pro",
    )
