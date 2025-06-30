import os
import logging

from dotenv import load_dotenv

from sqlalchemy.orm import Session

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

import constants
import helpers
from models import Enrollment, User, engine


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


ECHO = 1


@is_admin
async def start_echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"start_echo handler triggered by {helpers.get_user(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Send a message to echo."
    )
    return ECHO


@is_admin
async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"echo_message handler triggered by {helpers.get_user(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=update.message.text,
        entities=update.message.entities
    )
    return ConversationHandler.END


@is_admin
async def cancel_echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"cancel_echo handler triggered by {helpers.get_user(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Echo cancelled",
    )
    return ConversationHandler.END


BROADCAST = 1


@is_admin
async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"start_broadcast handler triggered by {helpers.get_user(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Send a message to broadcast"
    )
    return BROADCAST


@is_admin
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"broadcast handler triggered by {helpers.get_user(update)}")

    with Session(engine) as session:
        users = session.query(User).all()
        logging.info(f"got {len(users)} users from db for broadcasting")

    successful_count = 0
    fail_count = 0
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user.tg_id,
                text=update.message.text,
                entities=update.message.entities
            )
            successful_count += 1
        except Exception as e:
            logging.info(f"couldn't send broadcast message to {user.tg_username} {user.tg_id}: {e}")
            fail_count += 1

    logging.info(f"Successfully broadcast message to {successful_count} users, failed {fail_count} users.")
    return ConversationHandler.END


@is_admin
async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"cancel_broadcast handler triggered by {helpers.get_user(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Broadcast cancelled",
    )
    return ConversationHandler.END


async def do_broadcast_course(update: Update, context: ContextTypes.DEFAULT_TYPE, course_id) -> int:
    with Session(engine) as session:
        course_enrollments = session.query(Enrollment.tg_id).filter(Enrollment.course_id == course_id).all()
        tg_ids = [tg_id for (tg_id,) in course_enrollments]
        logging.info(f"got {len(tg_ids)} users from db for broadcasting for course {course_id}")

    successful_count = 0
    fail_count = 0
    for tg_id in tg_ids:
        try:
            await context.bot.send_message(
                chat_id=tg_id,
                text=update.message.text,
                entities=update.message.entities
            )
            successful_count += 1
        except Exception as e:
            logging.info(f"couldn't send broadcast for course {course_id} message to {tg_id}: {e}")
            fail_count += 1

    logging.info(f"Successfully broadcast for course {course_id} to {successful_count} users, failed {fail_count} users.")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Successfully broadcast for course {course_id} to {successful_count} users, failed {fail_count} users."
    )
    return ConversationHandler.END


LEETCODE_BROADCAST = 1


@is_admin
async def start_leetcode_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"start_leetcode_broadcast handler triggered by {helpers.get_user(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Send a message to broadcast to Leetcode users"
    )
    return LEETCODE_BROADCAST


@is_admin
async def leetcode_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"leetcode_broadcast handler triggered by {helpers.get_user(update)}")
    return await do_broadcast_course(update, context, constants.leetcode_course_id)


SRE_BROADCAST = 1


@is_admin
async def start_sre_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"start_sre_broadcast handler triggered by {helpers.get_user(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Send a message to broadcast to SRE users"
    )
    return SRE_BROADCAST


@is_admin
async def sre_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"sre_broadcast handler triggered by {helpers.get_user(update)}")
    return await do_broadcast_course(update, context, constants.sre_course_id)
