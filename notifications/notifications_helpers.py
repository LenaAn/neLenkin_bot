import logging
import os
from dotenv import load_dotenv

from telegram import InlineKeyboardMarkup
from telegram.ext import ContextTypes

notifications_logger = logging.getLogger(__name__)
notifications_logger.setLevel(logging.DEBUG)


async def do_send_notifications(context: ContextTypes.DEFAULT_TYPE, notification_chat_ids: list[str], message: str,
                                menu: InlineKeyboardMarkup, notification_name: str) -> None:
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

    notifications_logger.info(
        f"Successfully sent {notification_name} notification to {successful_count} users, failed {fail_count} users.")

    load_dotenv(override=True)
    admin_chat_id = int(os.getenv('ADMIN_CHAT_ID'))
    notifications_logger.debug(f"reloaded admin chat id: {admin_chat_id}")

    await context.bot.send_message(
        chat_id=admin_chat_id,
        text=f"Successfully sent {notification_name} notifications to {successful_count} users, failed {fail_count} "
             f"users."
    )
