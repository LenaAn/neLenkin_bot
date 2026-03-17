import logging
from telegram import Update
from telegram.ext import ContextTypes

import sqlalchemy
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import constants
import helpers
from models import MembershipByActivity, User, engine


HELP_TEXT = ("<b>Поддерживаемые команды:</b>\n"
             "/start — Главное меню\n"
             "/courses — Активные курсы 🐙\n"
             "/membership — Подписка 🌟\n"
             "/join — Вступить в клуб 🎩\n\n"
             ""
             "Если бот запутался в диалоге, поможет\n"
             "/cancel — Прервать любой диалог\n\n"
             ""
             "Запись на моки по Leetcode:\n"
             "/leetcode_register — Записаться на мок собеседование\n"
             "/cancel_leetcode_register — Отменить запись на мок собеседование\n\n"
             ""
             "По любым вопросам пишите Лене @lenka_colenka")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"start triggered by {helpers.repr_user_from_update(update)}")

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

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=constants.club_description + HELP_TEXT,
        parse_mode="HTML",
    )


async def command_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"help triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=HELP_TEXT,
        parse_mode="HTML",
    )


async def private_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"private message handler triggered by {helpers.repr_user_from_update(update)}: {update.message.text}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Я не понимаю сообщения, только эти команды:\n\n" + HELP_TEXT,
        parse_mode="HTML",
    )
