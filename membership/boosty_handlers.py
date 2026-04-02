import logging

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from telegram import Update
from telegram.ext import (CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler,
                          filters)

import helpers
import models
import settings
from membership import fetch_boosty_patrons, membership
from monitoring import calculate_metrics_and_report

CONNECT_BOOSTY = 1


async def start_connect_boosty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"start_connect_boosty handler triggered by {helpers.repr_user_from_update(update)}")
    if update.callback_query:
        await update.callback_query.answer()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Введи email, который привязан к твоему профилю Boosty. \nЕсли у профиля нет email, "
             f"введи имя профиля Boosty.\n\nЕсли не получается — напиши мне @lenka_colenka!"
    )
    return CONNECT_BOOSTY


# we will store it regardless it's a paying Boosty patron or not
# we just store the pairing of tg_id to Boosty user id
# to know if it's paying Boosty patron or not, check Redis
async def store_boosty_linking(update: Update, boosty_user_id: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    with Session(models.engine) as session:
        user = helpers.get_user(update)
        boosty_link = {
            'tg_id': user.id,
            'tg_username': user.username,
            'boosty_user_id': boosty_user_id
        }
        stmt = insert(models.BoostyLink).values(**boosty_link)
        stmt = stmt.on_conflict_do_update(
            constraint='BoostyLink_pkey',
            set_=boosty_link
        )
        session.execute(stmt)
        try:
            session.commit()
            logging.info(f"Added new Boosty linking: {user.username} to {boosty_user_id} to db")
        except Exception as e:
            # I don't rely on handlers.handlers.error_handler because in this case ConversationHandler.END will not be
            # returned and commands after this exception will be ignored
            session.rollback()
            logging.warning(f"Didn't add Boosty linking: {user.username} to {boosty_user_id} to db: {e}")
            await context.bot.send_message(
                chat_id=settings.ADMIN_CHAT_ID,
                text=f"Не смог прявязать Boosty профиль {boosty_user_id} к пользователю {user.username}: {e}"
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Упс! Случилась ошибка, но проблема не в тебе! Уже оповестил @lenka_colenka"
            )
            return False
    return True


async def do_connect_boosty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"do_connect handler triggered by {helpers.repr_user_from_update(update)}")

    user_input: str = update.message.text.strip()

    await fetch_boosty_patrons.load_boosty_patrons(context.bot)
    redis_result = fetch_boosty_patrons.get_boosty_info_by_field(user_input)

    if redis_result:
        boosty_user_id = redis_result[0]
        boosty_info = redis_result[1]
        if await store_boosty_linking(update, boosty_user_id, context):
            logging.info(f"Boosty found for user input {user_input}: {boosty_user_id}")
            msg: str = f"Нашла твой профиль Boosty: {user_input}.\n\n"
            boosty_price = int(boosty_info['price'])
            if boosty_price >= 1500:
                msg += f"Ты донатишь мне {boosty_price} рублей в месяц. Спасибо! 🥹"
            elif 0 < boosty_price < 1500:
                msg += (f"Ты донатишь мне {boosty_price} рублей в месяц. Чтобы получить "
                        f"Pro подписку, оформи донат на 1500 рублей в месяц 🥹")
            else:
                msg += (f"Ты пока не донатишь мне на Boosty. Чтобы получить Pro подписку, оформи донат на "
                        f"1500 рублей в месяц 🥹")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=msg,
            )
            await calculate_metrics_and_report.calculate_metrics_and_report(context.bot)
        else:
            return ConversationHandler.END
    else:
        logging.info(f"Could not find Boosty for user input {user_input}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Не нашла Boosty по {user_input}. Проверь, что все верно или напиши @lenka_colenka",
        )
    return ConversationHandler.END


async def cancel_connect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"cancel_connect handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Отмена привязки патрона",
    )
    return ConversationHandler.END


connect_boosty_handler = ConversationHandler(
    entry_points=[
        CommandHandler('connect_boosty', start_connect_boosty, filters.ChatType.PRIVATE),
        CallbackQueryHandler(start_connect_boosty, '^connect_boosty')
    ],
    states={CONNECT_BOOSTY: [
        MessageHandler(filters.TEXT & ~filters.COMMAND, do_connect_boosty),
        CallbackQueryHandler(start_connect_boosty, '^connect_boosty')
    ]},
    fallbacks=[
        CommandHandler('cancel_connect', cancel_connect),
        CommandHandler('cancel', cancel_connect),
    ],
)


async def disconnect_boosty_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"disconnect_boosty_handler triggered by {helpers.repr_user_from_update(update)}")

    with Session(models.engine) as session:
        tg_user = helpers.get_user(update)
        session.query(models.BoostyLink).filter(models.BoostyLink.tg_id == str(tg_user.id)).delete()
        session.commit()
        logging.info(f"Deleted Boosty linking for {tg_user.username}")
        await membership.handle_membership(update, context)
