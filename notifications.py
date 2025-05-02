import datetime
import logging
import os
from telegram.ext import ContextTypes

import constants
from dotenv import load_dotenv


notifications_logger = logging.getLogger(__name__)
notifications_logger.setLevel(logging.DEBUG)


async def handle_leetcode_notification(context: ContextTypes.DEFAULT_TYPE):
    # reloading chat ids because I want to change it on the fly
    load_dotenv(override=True)
    leetcode_chats_str = os.getenv('LEETCODE_NOTIFICATION_CHAT_IDS')
    leetcode_notification_chat_ids = [int(chat_id) for chat_id in leetcode_chats_str.split(",")]
    notifications_logger.debug(f"reloaded leetcode chat ids: {leetcode_notification_chat_ids}")

    for chat_id in leetcode_notification_chat_ids:
        notifications_logger.info(f"handle_leetcode_notification for chat {chat_id}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=constants.mock_leetcode_reminder,
            parse_mode="HTML")


async def register_leetcode_notifications(app):
        app.job_queue.run_daily(
            callback=handle_leetcode_notification,
            time=datetime.time(hour=15, minute=6, tzinfo=datetime.timezone.utc),  # 5:06 PM Belgrade time in Summer
            days=(4,),  # 0 = Sunday, ..., 4 = Thursday
            name=f"leetcode_notification"
        )
