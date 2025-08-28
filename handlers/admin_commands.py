import os
import logging

from dotenv import load_dotenv

from sqlalchemy.orm import Session

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

import constants
import helpers
import models


def is_admin_id(tg_id: int) -> bool:
    # reloading admin chat is because I want to change it on the fly
    load_dotenv(override=True)
    admin_chat_id = int(os.getenv('ADMIN_CHAT_ID'))
    logging.debug(f"reloaded admin chat id: {admin_chat_id}")
    return tg_id == admin_chat_id


def is_admin(callback):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if is_admin_id(update.effective_chat.id):
            logging.info(f"is_admin check triggered by {helpers.repr_user_from_update(update)}, user IS a admin")
            return await callback(update, context, *args, **kwargs)
        logging.info(f"is_admin check triggered by {helpers.repr_user_from_update(update)}, user IS NOT a admin")
        await update.effective_chat.send_message("❌ Для этого действия нужно быть админом")
        return None

    return wrapper


def is_any_curator(callback):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        logging.info(f"is_any_curator triggered by {helpers.repr_user_from_update(update)}")

        if is_admin_id(update.effective_chat.id):
            logging.info(f"{helpers.repr_user_from_update(update)} is admin so has power of curator")
            return await callback(update, context, *args, **kwargs)

        with Session(models.engine) as session:
            course_curator_tg_id = session.query(models.Course.curator_tg_id).all()
            course_curator_tg_id = [result[0] for result in course_curator_tg_id]  # smthng like [None, None, '1111111']
        logging.info(f"course_curator_tg_id is {course_curator_tg_id}")

        if str(update.effective_chat.id) in course_curator_tg_id:
            logging.info(f"{helpers.repr_user_from_update(update)} IS a curator")
            return await callback(update, context, *args, **kwargs)

        logging.info(f"{helpers.repr_user_from_update(update)} IS NOT a curator")
        await update.effective_chat.send_message("❌ Для этого действия нужно быть куратором какого-нибудь потока")
        return None

    return wrapper


def is_curator(course_id: int):
    def is_curator_for_course(callback):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            logging.info(f"is_curator_for_course triggered by {helpers.repr_user_from_update(update)} for "
                         f"{constants.id_to_course[course_id]}")

            if is_admin_id(update.effective_chat.id):
                logging.info(f"{helpers.repr_user_from_update(update)} is admin so has power of curator")
                return await callback(update, context, *args, **kwargs)

            with Session(models.engine) as session:
                course_curator_tg_id = session.query(models.Course.curator_tg_id).filter(
                    models.Course.id == course_id).all()
            if len(course_curator_tg_id) == 0 or len(course_curator_tg_id[0]) == 0:
                logging.info(f"{constants.id_to_course[course_id]} doesn't have a curator")
                await update.effective_chat.send_message("❌ Для этого действия нужно быть куратором потока")
                return None

            if str(update.effective_chat.id) in course_curator_tg_id[0]:
                logging.info(f"{helpers.repr_user_from_update(update)} IS a curator for "
                             f"{constants.id_to_course[course_id]}")
                return await callback(update, context, *args, **kwargs)

            logging.info(f"{helpers.repr_user_from_update(update)} IS NOT a curator for "
                         f"{constants.id_to_course[course_id]}")
            await update.effective_chat.send_message("❌ Для этого действия нужно быть куратором потока")
            return None

        return wrapper

    return is_curator_for_course


@is_admin
async def get_users_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"get_users handler triggered by {helpers.repr_user_from_update(update)}")

    with Session(models.engine) as session:
        users_count = session.query(models.User).count()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{users_count} users started the bot"
    )


@is_curator(constants.sre_course_id)
async def get_sre_users_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"get_sre_users handler triggered by {helpers.repr_user_from_update(update)}")

    with Session(models.engine) as session:
        sre_users_count = session.query(models.Enrollment.tg_id).filter(
            models.Enrollment.course_id == constants.sre_course_id).count()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{sre_users_count} users are enrolled in SRE"
    )


@is_curator(constants.grind_course_id)
async def get_grind_users_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"get_grind_users handler triggered by {helpers.repr_user_from_update(update)}")

    with Session(models.engine) as session:
        grind_users_count = session.query(models.Enrollment.tg_id).filter(
            models.Enrollment.course_id == constants.grind_course_id).count()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{grind_users_count} users are enrolled in Leetcode Grind"
    )


@is_curator(constants.ddia_4_course_id)
async def get_ddia_users_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"get_ddia_users_handler handler triggered by {helpers.repr_user_from_update(update)}")

    with Session(models.engine) as session:
        ddia_users_count = session.query(models.Enrollment.tg_id).filter(
            models.Enrollment.course_id == constants.ddia_4_course_id).count()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{ddia_users_count} users are enrolled in DDIA"
    )


ECHO = 1


# todo: now `is_sre_admin` means "root admin OR SRE admin", while `is_admin`means "only root admin". Rethink it
@is_any_curator
async def start_echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"start_echo handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Send a message to echo."
    )
    return ECHO


@is_any_curator
async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE, reply_markup: InlineKeyboardMarkup = None) \
        -> int:
    logging.info(f"echo_message handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=update.message.text,
        entities=update.message.entities,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    return ConversationHandler.END


@is_any_curator
async def cancel_echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"cancel_echo handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Echo cancelled",
    )
    return ConversationHandler.END


echo_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('echo', start_echo)],
    states={ECHO: [MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message)]},
    fallbacks=[CommandHandler('cancel_echo', cancel_echo)],
)

BROADCAST = 1


@is_admin
async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"start_broadcast handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Send a message to broadcast"
    )
    return BROADCAST


@is_admin
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE, reply_markup: InlineKeyboardMarkup = None) \
        -> int:
    logging.info(f"broadcast handler triggered by {helpers.repr_user_from_update(update)}")

    with Session(models.engine) as session:
        users = session.query(models.User).all()
        logging.info(f"got {len(users)} users from db for broadcast")

    successful_count = 0
    fail_count = 0
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user.tg_id,
                text=update.message.text,
                entities=update.message.entities,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            successful_count += 1
        except Exception as e:
            logging.info(f"couldn't send broadcast message to {user.tg_username} {user.tg_id}: {e}")
            fail_count += 1

    logging.info(f"Successfully broadcast message to {successful_count} users, failed {fail_count} users.")
    return ConversationHandler.END


@is_any_curator
async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"cancel_broadcast handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Broadcast cancelled",
    )
    return ConversationHandler.END


# todo: make sure it doesn't mess up with multiple admins
broadcast_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('broadcast', start_broadcast)],
    states={BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast)]},
    fallbacks=[CommandHandler('cancel_broadcast', cancel_broadcast)],
)


async def do_broadcast_course(update: Update, context: ContextTypes.DEFAULT_TYPE, course_id: int,
                              reply_markup: InlineKeyboardMarkup = None) -> int:
    logging.info(f"{constants.id_to_course[course_id]}_broadcast handler triggered by "
                 f"{helpers.repr_user_from_update(update)}")
    with Session(models.engine) as session:
        course_enrollments = session.query(models.Enrollment.tg_id).filter(
            models.Enrollment.course_id == course_id).all()
        tg_ids = [tg_id for (tg_id,) in course_enrollments]
        logging.info(f"got {len(tg_ids)} users from db for {constants.id_to_course[course_id]} broadcast")

    successful_count = 0
    fail_count = 0
    for tg_id in tg_ids:
        try:
            await context.bot.send_message(
                chat_id=tg_id,
                text=update.message.text,
                entities=update.message.entities,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            successful_count += 1
        except Exception as e:
            logging.info(f"couldn't send {constants.id_to_course[course_id]} broadcast message to {tg_id}: {e}")
            fail_count += 1

    logging.info(f"Successfully {constants.id_to_course[course_id]} broadcast to {successful_count} users, "
                 f"failed {fail_count} users.")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Successfully {constants.id_to_course[course_id]} broadcast to {successful_count} users, "
             f"failed {fail_count} users."
    )
    return ConversationHandler.END


LEETCODE_BROADCAST = 1


@is_admin
async def start_leetcode_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"start_leetcode_broadcast handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Send a message to broadcast to Leetcode users"
    )
    return LEETCODE_BROADCAST


@is_admin
async def leetcode_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await do_broadcast_course(update, context, constants.leetcode_course_id)


leetcode_broadcast_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('leetcode_broadcast', start_leetcode_broadcast)],
    states={LEETCODE_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, leetcode_broadcast)]},
    fallbacks=[CommandHandler('cancel_broadcast', cancel_broadcast)],
)

LEETCODE_NEW_TOPIC = 1


@is_admin
async def start_leetcode_new_topic_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"start_leetcode_new_topic_broadcast handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Send the new topic for Leetcode"
    )
    return LEETCODE_NEW_TOPIC


@is_admin
async def leetcode_new_topic_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    button_list = [
        InlineKeyboardButton("Записаться на моки!", callback_data="leetcode_register"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]

    return await do_broadcast_course(update, context, constants.leetcode_course_id, InlineKeyboardMarkup(menu))


leetcode_new_topic_broadcast = ConversationHandler(
    entry_points=[CommandHandler('leetcode_new_topic', start_leetcode_new_topic_broadcast)],
    states={LEETCODE_NEW_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, leetcode_new_topic_broadcast)]},
    fallbacks=[CommandHandler('cancel_broadcast', cancel_broadcast)],
)

SRE_BROADCAST = 1


@is_curator(constants.sre_course_id)
async def start_sre_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"start_sre_broadcast handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Send a message to broadcast to SRE users"
    )
    return SRE_BROADCAST


@is_curator(constants.sre_course_id)
async def sre_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await do_broadcast_course(update, context, constants.sre_course_id)


sre_broadcast_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('sre_broadcast', start_sre_broadcast)],
    states={SRE_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, sre_broadcast)]},
    fallbacks=[CommandHandler('cancel_broadcast', cancel_broadcast)],
)

DDIA_BROADCAST = 1


@is_curator(constants.ddia_4_course_id)
async def start_ddia_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"start_ddia_broadcast handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Send a message to broadcast to DDIA users"
    )
    return DDIA_BROADCAST


@is_curator(constants.ddia_4_course_id)
async def ddia_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await do_broadcast_course(update, context, constants.ddia_4_course_id)


ddia_broadcast_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('ddia_broadcast', start_ddia_broadcast)],
    states={DDIA_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ddia_broadcast)]},
    fallbacks=[CommandHandler('cancel_broadcast', cancel_broadcast)],
)


GRIND_BROADCAST = 1


@is_curator(constants.grind_course_id)
async def start_grind_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"start_grind_broadcast handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Send a message to broadcast to Leetcode Grind users"
    )
    return GRIND_BROADCAST


@is_curator(constants.grind_course_id)
async def grind_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await do_broadcast_course(update, context, constants.grind_course_id)


grind_broadcast_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('grind_broadcast', start_grind_broadcast)],
    states={GRIND_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, grind_broadcast)]},
    fallbacks=[CommandHandler('cancel_broadcast', cancel_broadcast)],
)


@is_admin
async def leetcode_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"leetcode_on handler triggered by {helpers.repr_user_from_update(update)}")
    models.leetcode_status_on = True

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="leetcode is ON" if models.leetcode_status_on else "leetcode is OFF"
    )


@is_admin
async def leetcode_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # todo: user may be in the middle of leetcode_register_handler. When leetcode status is turned off, the conversation
    #  should start from start for every user
    logging.info(f"leetcode_off handler triggered by {helpers.repr_user_from_update(update)}")
    models.leetcode_status_on = False

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="leetcode is ON" if models.leetcode_status_on else "leetcode is OFF"
    )


@is_curator(constants.sre_course_id)
async def sre_notification_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"sre_notification_on handler triggered by {helpers.repr_user_from_update(update)}")
    models.sre_notification_on = True

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="SRE notification is ON" if models.sre_notification_on else "SRE notification is OFF"
    )


@is_curator(constants.sre_course_id)
async def sre_notification_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"sre_notification_off handler triggered by {helpers.repr_user_from_update(update)}")
    models.sre_notification_on = False

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="SRE notification is ON" if models.sre_notification_on else "SRE notification is OFF"
    )
