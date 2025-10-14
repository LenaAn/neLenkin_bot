import logging

from telegram import Update
from telegram.ext import (CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters)

import helpers
from patreon import fetch_patrons

CONNECT_PATREON = 1


async def start_connect_patreon(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"start_connect_patreon handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Введи почту, которая привязана к твоему профилю Patreon."
    )
    return CONNECT_PATREON


async def connect_with_email(update: Update, context: ContextTypes.DEFAULT_TYPE) \
        -> int:
    logging.info(f"connect_with_email handler triggered by {helpers.repr_user_from_update(update)}")
    email_to_find = update.message.text.strip().lower()
    logging.info(f"looking for patron with email {email_to_find}")

    # this method loads patrons from patreon and does lookup in redis
    patron_info = fetch_patrons.get_patron_by_email(email_to_find)
    if patron_info:
        # todo: analyze if this is a paying and active patron
        logging.info(f"Patron found for email {email_to_find}: {patron_info}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Нашла патрона! {patron_info}",
        )
    else:
        logging.info(f"Could not find patron for email {email_to_find}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Не нашла патрона по email {email_to_find}. Проверь, что все верно или напиши @lenka_colenka",
        )
    return ConversationHandler.END


async def cancel_connect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"cancel_connect handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Отмена привязки патрона",
    )
    return ConversationHandler.END


connect_patreon_handler = ConversationHandler(
    entry_points=[CommandHandler('connect_patreon', start_connect_patreon)],
    states={CONNECT_PATREON: [MessageHandler(filters.TEXT & ~filters.COMMAND, connect_with_email)]},
    fallbacks=[CommandHandler('cancel_connect', cancel_connect)],
)
