import datetime
import logging
import os
from dotenv import load_dotenv

from sqlalchemy.orm import Session
from telegram.ext import ContextTypes

import constants
from models import Enrollment, engine

notifications_logger = logging.getLogger(__name__)
notifications_logger.setLevel(logging.DEBUG)


async def register_notifications(application):
    await register_leetcode_notifications(application)
    await register_sre_notifications(application)


async def handle_notification(context: ContextTypes.DEFAULT_TYPE):
    course_id: int = context.job.data["course_id"]
    message: str = context.job.data["message"]
    with Session(engine) as session:
        result = session.query(Enrollment.tg_id).filter(Enrollment.course_id == course_id).all()
        notification_chat_ids = [item[0] for item in result]
    notifications_logger.debug(f"handling notifications for course {course_id}, "
                               f"got {len(notification_chat_ids)} chat ids")

    successful_count = 0
    fail_count = 0
    for chat_id in notification_chat_ids:
        notifications_logger.info(f"notification_chat_ids for chat {chat_id}")
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="HTML")
            successful_count += 1
        except Exception as e:
            notifications_logger.info(f"failed to send notification to chat {chat_id}: {e}")
            fail_count += 1

    logging.info(f"Successfully sent notifications for course {course_id} to {successful_count} users, "
                 f"failed {fail_count} users.")

    load_dotenv(override=True)
    admin_chat_id = int(os.getenv('ADMIN_CHAT_ID'))
    logging.debug(f"reloaded admin chat id: {admin_chat_id}")

    await context.bot.send_message(
        chat_id=admin_chat_id,
        text=f"Successfully sent notifications for course {course_id} to {successful_count} users, "
             f"failed {fail_count} users."
    )


async def register_leetcode_notifications(app):
    app.job_queue.run_daily(
        callback=handle_notification,
        time=datetime.time(hour=15, minute=6, tzinfo=datetime.timezone.utc),  # 5:06 PM Belgrade time in Summer
        days=(4,),  # 0 = Sunday, ..., 4 = Thursday
        name=f"leetcode_notification",
        data={"course_id": constants.leetcode_course_id, "message": constants.mock_leetcode_reminder}
    )


async def register_sre_notifications(app):
    app.job_queue.run_daily(
        callback=handle_notification,
        time=datetime.time(hour=15, minute=55, tzinfo=datetime.timezone.utc),  # 5:55 PM Belgrade time in Summer
        days=(2,),  # 0 = Sunday, 2 = Tuesday
        name=f"sre_notification",
        data={"course_id": constants.sre_course_id, "message": constants.sre_reminder}
    )
