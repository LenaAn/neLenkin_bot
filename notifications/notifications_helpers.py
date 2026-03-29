import logging
import os
from dotenv import load_dotenv

from telegram import InlineKeyboardMarkup
from telegram.ext import ContextTypes

from monitoring import update_users_in_db

notifications_logger = logging.getLogger(__name__)
notifications_logger.setLevel(logging.DEBUG)


async def do_send_notifications(context: ContextTypes.DEFAULT_TYPE, notification_chat_ids: list[str], message: str,
                                menu: InlineKeyboardMarkup, notification_name: str) -> None:
    successful_count = 0
    failed_ids = []
    for chat_id in notification_chat_ids:
        if (successful_count + len(failed_ids)) % 50 == 0:
            notifications_logger.info(f"Notification broadcast in progress: {successful_count} successful, "
                                      f"{len(failed_ids)} failed so far")
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="HTML",
                reply_markup=menu)
            successful_count += 1
        except Exception as e:
            failed_ids.append(chat_id)

    notifications_logger.info(f"Successfully sent {notification_name} notification to {successful_count} users, "
                              f"failed {len(failed_ids)} users.")

    success_ids = list(set(notification_chat_ids) - set(failed_ids))
    await update_users_in_db.update_users_after_broadcast(success_ids, failed_ids)

    load_dotenv(override=True)
    admin_chat_id = int(os.getenv('ADMIN_CHAT_ID'))
    notifications_logger.debug(f"reloaded admin chat id: {admin_chat_id}")

    await context.bot.send_message(
        chat_id=admin_chat_id,
        text=f"Successfully sent {notification_name} notifications to {successful_count} users, "
             f"failed {len(failed_ids)} users."
    )
