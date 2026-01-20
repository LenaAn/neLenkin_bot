import datetime
import os
import logging

from dotenv import load_dotenv

import sqlalchemy
from sqlalchemy.orm import Session

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

import constants
import helpers
import models
from patreon import fetch_patrons
import membership


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


@is_admin
async def get_patrons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"get_patrons handler triggered by {helpers.repr_user_from_update(update)}")

    await fetch_patrons.load_patrons(context.bot)
    active_patrons = fetch_patrons.get_patrons_from_redis("active_patron")
    logging.info(f"active_patrons are {active_patrons}")
    active_patrons_count = len(active_patrons)
    total_sum = sum(int(patron[1]) for patron in active_patrons)
    patrons_str = "\n".join([', '.join(patron) for patron in active_patrons])
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"You have {active_patrons_count} active patrons with total sum of ${total_sum // 100}:\n\n{patrons_str}"
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


@is_curator(constants.dmls_course_id)
async def get_dmls_users_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"get_dmls_users_handler handler triggered by {helpers.repr_user_from_update(update)}")

    with Session(models.engine) as session:
        dmls_users_count = session.query(models.Enrollment.tg_id).filter(
            models.Enrollment.course_id == constants.dmls_course_id).count()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{dmls_users_count} users are enrolled in DMLS"
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
    await context.bot.copy_message(
        chat_id=update.effective_chat.id,
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id,
        reply_markup=reply_markup
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
    entry_points=[CommandHandler('echo', start_echo, filters.ChatType.PRIVATE)],
    states={ECHO: [MessageHandler(~filters.COMMAND, echo_message)]},
    fallbacks=[
        CommandHandler('cancel_echo', cancel_echo),
        CommandHandler('cancel', cancel_echo),
    ],
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
            await context.bot.copy_message(
                chat_id=user.tg_id,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
                reply_markup=reply_markup
            )
            successful_count += 1
        except Exception as e:
            logging.info(f"couldn't send broadcast message to {user.tg_username} {user.tg_id}: {e}")
            fail_count += 1

    logging.info(f"Successfully broadcast message to {successful_count} users, failed {fail_count} users.")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Successfully broadcast to {successful_count} users, failed {fail_count} users."
    )
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
    entry_points=[CommandHandler('broadcast', start_broadcast, filters.ChatType.PRIVATE)],
    states={BROADCAST: [MessageHandler(~filters.COMMAND, broadcast)]},
    fallbacks=[
        CommandHandler('cancel_broadcast', cancel_broadcast),
        CommandHandler('cancel', cancel_broadcast),
    ],
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
            await context.bot.copy_message(
                chat_id=tg_id,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
                reply_markup=reply_markup
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
    entry_points=[CommandHandler('leetcode_broadcast', start_leetcode_broadcast, filters.ChatType.PRIVATE)],
    states={LEETCODE_BROADCAST: [MessageHandler(~filters.COMMAND, leetcode_broadcast)]},
    fallbacks=[
        CommandHandler('cancel_broadcast', cancel_broadcast),
        CommandHandler('cancel', cancel_broadcast)
    ],
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
    entry_points=[CommandHandler('leetcode_new_topic', start_leetcode_new_topic_broadcast, filters.ChatType.PRIVATE)],
    states={LEETCODE_NEW_TOPIC: [MessageHandler(~filters.COMMAND, leetcode_new_topic_broadcast)]},
    fallbacks=[
        CommandHandler('cancel_broadcast', cancel_broadcast),
        CommandHandler('cancel', cancel_broadcast)
    ],
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
    entry_points=[CommandHandler('sre_broadcast', start_sre_broadcast, filters.ChatType.PRIVATE)],
    states={SRE_BROADCAST: [MessageHandler(~filters.COMMAND, sre_broadcast)]},
    fallbacks=[
        CommandHandler('cancel_broadcast', cancel_broadcast),
        CommandHandler('cancel', cancel_broadcast)],
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
    entry_points=[CommandHandler('ddia_broadcast', start_ddia_broadcast, filters.ChatType.PRIVATE)],
    states={DDIA_BROADCAST: [MessageHandler(~filters.COMMAND, ddia_broadcast)]},
    fallbacks=[
        CommandHandler('cancel_broadcast', cancel_broadcast),
        CommandHandler('cancel', cancel_broadcast),
    ],
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
    entry_points=[CommandHandler('grind_broadcast', start_grind_broadcast, filters.ChatType.PRIVATE)],
    states={GRIND_BROADCAST: [MessageHandler(~filters.COMMAND, grind_broadcast)]},
    fallbacks=[
        CommandHandler('cancel_broadcast', cancel_broadcast),
        CommandHandler('cancel', cancel_broadcast)
    ],
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


@is_curator(constants.ddia_4_course_id)
async def ddia_notification_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"ddia_notification_on handler triggered by {helpers.repr_user_from_update(update)}")
    models.ddia_notification_on = True

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="DDIA notification is ON" if models.ddia_notification_on else "DDIA notification is OFF"
    )


@is_curator(constants.ddia_4_course_id)
async def ddia_notification_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"ddia_notification_off handler triggered by {helpers.repr_user_from_update(update)}")
    models.ddia_notification_on = False

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="DDIA notification is ON" if models.ddia_notification_on else "DDIA notification is OFF"
    )


@is_curator(constants.codecrafters_course_id)
async def codecrafters_notification_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"codecrafters_notification_on handler triggered by {helpers.repr_user_from_update(update)}")
    models.codecrafters_notification_on = True

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="CodeCrafters notification is ON" if models.codecrafters_notification_on else "CodeCrafters notification is OFF"
    )


@is_curator(constants.codecrafters_course_id)
async def codecrafters_notification_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"codecrafters_notification_off handler triggered by {helpers.repr_user_from_update(update)}")
    models.codecrafters_notification_on = False

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="CodeCrafters notification is ON" if models.codecrafters_notification_on else "CodeCrafters notification is OFF"
    )


@is_admin
async def aoc_notification_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"aoc_notification_on handler triggered by {helpers.repr_user_from_update(update)}")
    models.aoc_notification_on = True

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="aoc is ON",
    )


@is_admin
async def aoc_notification_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"aoc_notification_off handler triggered by {helpers.repr_user_from_update(update)}")
    models.aoc_notification_on = False

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="aoc is OFF",
    )


@is_admin
async def pro_courses_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"pro_courses_on handler triggered by {helpers.repr_user_from_update(update)}")
    models.pro_courses_on = True

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="PRO coursee are ON" if models.pro_courses_on else "PRO courses are OFF"
    )


@is_admin
async def pro_courses_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"pro_courses_off handler triggered by {helpers.repr_user_from_update(update)}")
    models.pro_courses_on = False

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="PRO coursee are ON" if models.pro_courses_on else "PRO courses are OFF"
    )

# This method is of limited functionality because not every telegram user has a username.
# Currently, in order to present, one has to sign up to a spreadsheet with their tg_id, so I guess this should be good
# enough. If it's impossible to track down user by tg username, admin manual operation is required.
# Usage: /add_days lenka_colenka 30

# if no user in User table -- insert in MembershipByActivity table without tg_id
# if user in Users table
#    if already in MembershipByActivity and expiry = NULL, don't do anything
#    if already in MembershipByActivity and expiry != NULL, add days
@is_admin
async def add_days_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    if len(args) != 2:
        await update.message.reply_text("Usage: /add_days <username> <number>")
        return

    username = args[0]
    try:
        days = int(args[1])
        assert days > 0, "Number of days must be positive"
        assert days < 365 * 10, ("Can't add more than 10 year of membership. If you need to add more days, please add "
                                 "an infinite membership for user.")
    except Exception as e:
        await update.message.reply_text(f"Invalid number of days: {e}")
        return

    tg_id = None
    with (Session(models.engine) as session):
        try:
            tg_id = session.query(models.User.tg_id).filter(models.User.tg_username == username).first()[0]
            logging.info(f"got member from Users table: {tg_id}")
        except Exception as e:
            logging.info(f"Adding days to {username}, but there's no such User. Will add to MembershipByActivity "
                         f"without tg_id: {e}")
            await update.message.reply_text(f"Adding days to {username}, but there's no such User. Will add to "
                                            f"MembershipByActivity without tg_id: {e}")

    with (Session(models.engine) as session):
        if tg_id is not None:
            existing = session.query(models.MembershipByActivity
                                     ).filter(models.MembershipByActivity.tg_id == tg_id).first()
        else:
            existing = session.query(models.MembershipByActivity
                                     ).filter(models.MembershipByActivity.tg_username == username).first()

        if existing and not existing.expires_at:
            logging.info(f"User {username} has infinite membership by activity, no days added")
            await update.message.reply_text(f"User {username} has infinite membership by activity, no days added")
            return

        if existing and existing.expires_at > datetime.date.today():
            current_expiry = existing.expires_at
        else:
            current_expiry = datetime.date.today()

        new_expiry = current_expiry + datetime.timedelta(days=days)

        if existing:
            if tg_id is not None:
                stmt = (sqlalchemy.update(models.MembershipByActivity)
                        .where(models.MembershipByActivity.tg_id == tg_id)
                        .values(expires_at=new_expiry))
            else:
                stmt = (sqlalchemy.update(models.MembershipByActivity)
                        .where(models.MembershipByActivity.tg_username == username)
                        .values(expires_at=new_expiry))
        else:
            stmt = (
                sqlalchemy.insert(models.MembershipByActivity)
                .values(
                    tg_id=tg_id,
                    tg_username=username,
                    expires_at=new_expiry,
                )
            )

        session.execute(stmt)
        session.commit()
        logging.info(f"new membership expiry for {username}: {new_expiry}")

    try:
        await context.bot.send_message(
            chat_id=tg_id,
            text=f"Тебе добавили {days} дней 💜Pro подписки за активное участие в клубе!\n\n"
                 f"Твоя Pro подписка за активность истекает {new_expiry}.\n\n"
                 f"💜Pro подписка дает доступ ко всем возможностям клуба: неограниченные звонки с обсуждениями книг, "
                 f"leetcode моки, Random Coffee встречи и другое!\n\n"
                 f"Чтобы сохранить 💜Pro подписку, сделай презентацию либо подпишись на "
                 f"<a href='https://www.patreon.com/c/LenaAnyusha'>Patreon</a> хотя бы на $15 в месяц.\n\n"
                 f" Спасибо и keep being amazing!",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"Couldn't send an update to {username}: {e}")

    await update.message.reply_text(f"Added {days} days to {username}'s membership, new membership expiration is "
                                    f"{new_expiry}")


@is_admin
async def get_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"get_status_handler handler triggered by {helpers.repr_user_from_update(update)}")

    args = context.args

    if len(args) != 1:
        await update.message.reply_text("Usage: /get_status <username>")
        return

    username = args[0]

    # get tg_id from Users
    with (Session(models.engine) as session):
        try:
            tg_id = session.query(models.User.tg_id).filter(models.User.tg_username == username).first()[0]
            logging.info(f"got member from Users table: {tg_id}")
        except Exception as e:
            logging.info(f"There's no user with username {username}, not returning status for the user.")
            await update.message.reply_text(f"There's no user with username {username}, not returning status for the "
                                            f"user: {e}")
            return

    membership_info = membership.get_user_membership_info(tg_id, username)
    logging.info(f"Status for {username}: {membership_info}")
    await update.message.reply_text(f"Status for {username}:\n\n{membership_info}")
