import datetime
import logging

from sqlalchemy.orm import Session
from telegram.ext import ContextTypes

import constants
from models import Enrollment, engine

notifications_logger = logging.getLogger(__name__)
notifications_logger.setLevel(logging.DEBUG)


async def handle_leetcode_notification(context: ContextTypes.DEFAULT_TYPE):
    with Session(engine) as session:
        result = session.query(Enrollment.tg_id).filter(Enrollment.course_id == 7).all()
        leetcode_notification_chat_ids = [item[0] for item in result]
    notifications_logger.debug(f"got leetcode chat ids from db: {leetcode_notification_chat_ids}")

    for chat_id in leetcode_notification_chat_ids:
        notifications_logger.info(f"handle_leetcode_notification for chat {chat_id}")
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=constants.mock_leetcode_reminder,
                parse_mode="HTML")
        except Exception as e:
            notifications_logger.info(f"failed to send notification to chat {chat_id}: {e}")


async def register_leetcode_notifications(app):
        app.job_queue.run_daily(
            callback=handle_leetcode_notification,
            time=datetime.time(hour=15, minute=6, tzinfo=datetime.timezone.utc),  # 5:06 PM Belgrade time in Summer
            days=(4,),  # 0 = Sunday, ..., 4 = Thursday
            name=f"leetcode_notification"
        )
