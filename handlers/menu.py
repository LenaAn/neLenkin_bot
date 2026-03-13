import logging
from telegram import Update
from telegram.ext import ContextTypes

import sqlalchemy
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import constants
import helpers
from models import MembershipByActivity, User, engine


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"start triggered by {helpers.repr_user_from_update(update)}")
    # todo: just return the description and available commands
    # don't return the menu
    # the behavior will be the same as /help
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=constants.club_description,
        reply_markup=helpers.main_menu()
    )
    tg_user = helpers.get_user(update)
    with Session(engine) as session:
        user = User(
            tg_id=tg_user.id,
            tg_username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name
        )
        session.add(user)
        try:
            session.commit()
            logging.info(f"Added new user {tg_user.username} to db")
        except IntegrityError:
            session.rollback()
            logging.info(f"Didn't add {tg_user.username} to db, it already exists")
        except Exception as e:
            session.rollback()
            logging.warning(f"Couldn't add new user: {e}")

    with Session(engine) as session:
        existing_mba = session.query(MembershipByActivity).filter(
            MembershipByActivity.tg_username == tg_user.username
        ).first()

        if existing_mba:
            # user is a Member by activity but it's the first time they start the bot
            if existing_mba.tg_id is None:
                # todo: check that both for null and non-null expiry time works
                stmt = (sqlalchemy.update(MembershipByActivity)
                        .where(MembershipByActivity.tg_username == tg_user.username)
                        .values(tg_id=tg_user.id))
                session.execute(stmt)
                session.commit()
                logging.info(f"User {helpers.repr_user_from_update(update)} has a membership by activity, back-filling "
                             f"tg_id in MembershipByActivity")


async def command_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"help triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Бот находится в стадии разработки, пожалуйста не ломайте его 🥺.\n"
             "Если бот плохо себя ведет, пожалуйста напишите Ленке @lenka_colenka.\n\n"
             "Поддерживаемые команды:\n"
             "/start — Главное меню\n"
             "/help — Справка\n"
             "/cancel — Прервать любой диалог\n"
             "/leetcode_register — Записаться на мок собеседование по Leetcode\n"
             "/cancel_leetcode_register — Отменить запись на мок собеседование по Leetcode\n"
             "/connect_patreon — Привязать Patreon аккаунт"
    )


async def private_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"private message handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Я не понимаю сообщения, только эти две команды:\n"
             "/start — Главное меню\n"
             "/help — Справка"
    )
