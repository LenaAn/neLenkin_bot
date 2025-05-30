import os
import logging

from dotenv import load_dotenv

from sqlalchemy.orm import Session

from telegram import Update
from telegram.ext import ContextTypes

import helpers
from models import User, engine


def is_admin(callback):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # reloading admin chat is because I want to change it on the fly
        load_dotenv(override=True)
        admin_chat_id = int(os.getenv('ADMIN_CHAT_ID'))
        logging.debug(f"reloaded admin chat id: {admin_chat_id}")

        if update.effective_chat.id != admin_chat_id:
            logging.info(f"is_admin check triggered by {helpers.get_user(update)}, user IS NOT a moderator")
            await update.effective_chat.send_message("❌ Для этого действия нужно быть админом")
            return None
        logging.info(f"is_admin check triggered by {helpers.get_user(update)}, user IS a moderator")
        return await callback(update, context, *args, **kwargs)

    return wrapper


@is_admin
async def get_users_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"get_users handler triggered by {helpers.get_user(update)}")

    with Session(engine) as session:
        users_count = session.query(User).count()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{users_count} users started the bot"
    )
