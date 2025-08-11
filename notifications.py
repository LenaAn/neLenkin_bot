import datetime
import logging
import os
from dotenv import load_dotenv

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import constants
import models
from models import Enrollment, ScheduledPartMessages, engine

notifications_logger = logging.getLogger(__name__)
notifications_logger.setLevel(logging.DEBUG)


async def register_notifications(application):
    await register_leetcode_notifications(application)
    await register_sre_notifications(application)
    await register_ddia_notifications(application)


async def handle_notification(context: ContextTypes.DEFAULT_TYPE):
    course_id: int = context.job.data["course_id"]
    message: str = context.job.data["message"]
    menu: InlineKeyboardMarkup = context.job.data["menu"] if "menu" in context.job.data else None
    with Session(engine) as session:
        result = session.query(Enrollment.tg_id).filter(Enrollment.course_id == course_id).all()
        notification_chat_ids = [item[0] for item in result]
    notifications_logger.debug(f"handling {constants.id_to_course[course_id]} notification, "
                               f"got {len(notification_chat_ids)} chat ids")

    successful_count = 0
    fail_count = 0
    for chat_id in notification_chat_ids:
        notifications_logger.info(f"notification_chat_ids for chat {chat_id}")
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="HTML",
                reply_markup=menu)
            successful_count += 1
        except Exception as e:
            notifications_logger.info(f"failed to send notification to chat {chat_id}: {e}")
            fail_count += 1

    logging.info(f"Successfully sent {constants.id_to_course[course_id]} notification to {successful_count} users,"
                 f" failed {fail_count} users.")

    load_dotenv(override=True)
    admin_chat_id = int(os.getenv('ADMIN_CHAT_ID'))
    logging.debug(f"reloaded admin chat id: {admin_chat_id}")

    await context.bot.send_message(
        chat_id=admin_chat_id,
        text=f"Successfully sent {constants.id_to_course[course_id]} notifications to {successful_count} users, "
             f"failed {fail_count} users."
    )


async def register_leetcode_notifications(app):
    app.job_queue.run_daily(
        callback=handle_notification,
        time=datetime.time(hour=15, minute=6, tzinfo=datetime.timezone.utc),  # 5:06 PM Belgrade time in Summer
        days=(4,),  # 0 = Sunday, ..., 4 = Thursday
        name=f"leetcode_notification",
        data={
            "course_id": constants.leetcode_course_id,
            "message": constants.mock_leetcode_reminder,
            "menu": InlineKeyboardMarkup([[InlineKeyboardButton("Записаться на моки!", callback_data="leetcode_register")]])
        }
    )


async def handle_sre_notification(context: ContextTypes.DEFAULT_TYPE):
    # todo: we need more nice way of working with feature flags
    # you can't do `from models import sre_notification_on` and use just `sre_notification_on` here
    # because when you import variable from module, it creates a local copy
    if models.sre_notification_on:
        await handle_notification(context)
    else:
        logging.info("SRE notification is turned off, skipping sending SRE notifications")


async def handle_ddia_notification(context: ContextTypes.DEFAULT_TYPE):
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
            logging.debug(f"reloaded admin chat id: {admin_chat_id}")

            await context.bot.send_message(
                chat_id=admin_chat_id,
                text=f"Zoom link for DDIA not found for today!"
            )
            logging.error('Zoom link for DDIA not found for today!', exc_info=e)
            return

        print(f'call_link is {call_link}')

    context.job.data["message"] = f"Обсуждаем Designing Data-Intensive Applications через 5 минут!\n\n{call_link}"
    await handle_notification(context)


async def register_sre_notifications(app):
    app.job_queue.run_daily(
        callback=handle_sre_notification,
        time=datetime.time(hour=15, minute=55, tzinfo=datetime.timezone.utc),  # 5:55 PM Belgrade time in Summer
        days=(2,),  # 0 = Sunday, 2 = Tuesday
        name=f"sre_notification",
        data={"course_id": constants.sre_course_id, "message": constants.sre_reminder}
    )


async def register_ddia_notifications(app):
    app.job_queue.run_daily(
        callback=handle_ddia_notification,
        time=datetime.time(hour=15, minute=53, tzinfo=datetime.timezone.utc),  # 5:53 PM Belgrade time in Summer
        days=(4,),  # 0 = Sunday, 4 = Thursday
        name=f"ddia_notification",
        data={"course_id": constants.ddia_4_course_id}
    )
