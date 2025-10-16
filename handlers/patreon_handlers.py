import logging

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from telegram import Update
from telegram.ext import (CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters)

import helpers
import models
import settings
from patreon import fetch_patrons
from membership import get_level_from_patreon_info

CONNECT_PATREON = 1


async def start_connect_patreon(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"start_connect_patreon handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Введи почту, которая привязана к твоему профилю Patreon."
    )
    return CONNECT_PATREON


# we will store it regardless it's a paying patron or not
# we just store the pairing of tg_id to patreon email
# to know if it's paying patron or not, check redis
async def store_patreon_linking(update: Update, patron_email: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    with Session(models.engine) as session:
        user = helpers.get_user(update)
        patreon_link = {
            'tg_id': user.id,
            'tg_username': user.username,
            'patreon_email': patron_email
        }
        stmt = insert(models.PatreonLink).values(**patreon_link)
        stmt = stmt.on_conflict_do_update(
            constraint='PatreonLink_pkey',
            set_=patreon_link
        )
        session.execute(stmt)
        try:
            session.commit()
            logging.info(f"Added new patron linking: {user.username} to {patron_email} to db")
        except Exception as e:
            # I don't rely on handlers.handlers.error_handler because in this case ConversationHandler.END will not be
            # returned and commands after this exception will be ignored
            session.rollback()
            logging.warning(f"Didn't add patron linking: {user.username} to {patron_email} to db: {e}")
            await context.bot.send_message(
                chat_id=settings.ADMIN_CHAT_ID,
                text=f"Не смог прявязать Patreon почту {patron_email} к пользователю {user.username}: {e}"
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Упс! Случилась ошибка, но проблема не в тебе! Уже оповестил @lenka_colenka"
            )
            return False
    return True


async def connect_with_email(update: Update, context: ContextTypes.DEFAULT_TYPE) \
        -> int:
    logging.info(f"connect_with_email handler triggered by {helpers.repr_user_from_update(update)}")
    email_to_find = update.message.text.strip().lower()
    logging.info(f"looking for patron with email {email_to_find}")

    # this method loads patrons from patreon and does lookup in redis
    patron_info = fetch_patrons.get_patron_by_email(email_to_find)
    if patron_info:
        if await store_patreon_linking(update, email_to_find, context):
            # todo: analyze if this is a paying and active patron
            logging.info(f"Patron found for email {email_to_find}: {patron_info}")
            membership_level = get_level_from_patreon_info(patron_info)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"{membership_level.description}",
            )
        else:
            return ConversationHandler.END
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
