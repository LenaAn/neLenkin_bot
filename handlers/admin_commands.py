import datetime
import os
import logging

from dotenv import load_dotenv

import sqlalchemy
from sqlalchemy.orm import Session

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

import constants
import helpers
import models
from monitoring import push_monitoring, update_users_in_db
from membership import fetch_patrons, fetch_boosty_patrons, membership


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


def is_curator_for_course_in_context(callback):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        course_id = context.user_data["broadcast_to_course"]
        logging.info(f"is_curator_for_course_in_context triggered by {helpers.repr_user_from_update(update)} for "
                     f"{constants.id_to_course[course_id]}")

        if is_admin_id(update.effective_chat.id):
            logging.info(f"{helpers.repr_user_from_update(update)} is admin so has power of curator")
            return await callback(update, context)

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
            return await callback(update, context)

        logging.info(f"{helpers.repr_user_from_update(update)} IS NOT a curator for "
                     f"{constants.id_to_course[course_id]}")
        await update.effective_chat.send_message("❌ Для этого действия нужно быть куратором потока")
        return None

    return wrapper


@is_admin
async def get_users_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"get_users handler triggered by {helpers.repr_user_from_update(update)}")

    with Session(models.engine) as session:
        users_count = session.query(models.User).count()

    push_monitoring.metrics.set("users_started_bot", users_count)
    push_monitoring.metrics.push()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{users_count} users started the bot"
    )


async def get_patreon_summary(context: ContextTypes.DEFAULT_TYPE) -> (int, str):
    await fetch_patrons.load_patrons(context.bot)
    active_patreon_patrons = fetch_patrons.get_patrons_from_redis("active_patron")
    logging.info(f"active_patrons are {active_patreon_patrons}")
    active_patrons_count = len(active_patreon_patrons)
    patreon_total_sum = sum(int(patron[1]) for patron in active_patreon_patrons)
    patreon_subscribers_str = "\n - ".join([', '.join(patron) for patron in active_patreon_patrons])
    return active_patrons_count, (f"You have {active_patrons_count} active Patreon patrons with total sum of "
                                  f"${patreon_total_sum // 100}:\n\n - {patreon_subscribers_str}")


async def get_boosty_summary(context: ContextTypes.DEFAULT_TYPE) -> (int, str):
    await fetch_boosty_patrons.load_boosty_patrons(context.bot)
    active_boosty_patrons = fetch_boosty_patrons.get_boosty_patrons_from_redis(min_price_rub=1500)

    logging.info(f"active_boosty_patrons are {active_boosty_patrons}")
    active_boosty_patrons_count = len(active_boosty_patrons)
    boosty_total_sum = sum(int(patron[2]) for patron in active_boosty_patrons)
    boosty_subscribers_str = "\n - ".join([', '.join(patron) for patron in active_boosty_patrons])
    return active_boosty_patrons_count, (f"You have {active_boosty_patrons_count} paid Boosty patrons with total sum "
                                         f"of {boosty_total_sum} RUB:\n\n - {boosty_subscribers_str}")


@is_admin
async def get_patrons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"get_patrons handler triggered by {helpers.repr_user_from_update(update)}")
    patreon_count, patreon_summary = await get_patreon_summary(context)
    boosty_count, boosty_summary = await get_boosty_summary(context)

    push_monitoring.metrics.set("patreon_patrons", patreon_count)
    push_monitoring.metrics.set("boosty_patrons", boosty_count)
    push_monitoring.metrics.push()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{patreon_summary}\n\n{boosty_summary}"
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
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE, reply_markup: InlineKeyboardMarkup = None,
                    membership_filter: membership.MembershipLevel = None) \
        -> int:
    logging.info(f"broadcast handler triggered by {helpers.repr_user_from_update(update)}")

    with Session(models.engine) as session:
        users = session.query(models.User).all()
        logging.info(f"got {len(users)} users from db for broadcast")

    if membership_filter:
        users = [user for user in users if
                 membership.get_user_membership_info(user.tg_id).get_overall_level() == membership_filter]
        logging.info(f"got {len(users)} after filtering for {membership_filter} membership")

    successful_count = 0
    failed_ids = []
    for user in users:
        if (successful_count + len(failed_ids)) % 50 == 0:
            logging.info(f"Notification broadcast in progress: {successful_count} successful, "
                         f"{len(failed_ids)} failed so far")
        try:
            await context.bot.copy_message(
                chat_id=user.tg_id,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
                reply_markup=reply_markup
            )
            successful_count += 1
        except Exception as e:
            failed_ids.append(user.tg_id)

    success_ids = list(set([user.tg_id for user in users]) - set(failed_ids))
    await update_users_in_db.update_users_after_broadcast(success_ids, failed_ids)

    # todo: maybe don't push metrics here. I recorded in db to whom failed, maybe that's enough
    # will push metrics later in batch?
    push_monitoring.metrics.set("users_started_bot", len(users))
    push_monitoring.metrics.set("users_failed_broadcast", len(failed_ids))
    push_monitoring.metrics.push()

    logging.info(f"Successfully broadcast message to {successful_count} users, failed {len(failed_ids)} users.")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Successfully broadcast to {successful_count} users, failed {len(failed_ids)} users."
    )
    return ConversationHandler.END


@is_any_curator
async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"cancel_broadcast handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Broadcast cancelled",
    )
    clear_state(context)
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


BROADCAST_BASIC_MEMBERS = 1


@is_admin
async def start_broadcast_basic_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"start_broadcast_basic_members handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Send a message to broadcast to BASIC members"
    )
    return BROADCAST_BASIC_MEMBERS


@is_admin
async def broadcast_basic_members(update: Update, context: ContextTypes.DEFAULT_TYPE, reply_markup: InlineKeyboardMarkup = None) \
        -> int:
    logging.info(f"broadcast_basic_members handler triggered by {helpers.repr_user_from_update(update)}")
    return await broadcast(update, context, reply_markup, membership.basic)


@is_any_curator
async def cancel_broadcast_basic_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"cancel_broadcast_basic_members handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Broadcast to BASIC members cancelled",
    )
    return ConversationHandler.END


basic_members_broadcast_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('broadcast_basic_members', start_broadcast_basic_members, filters.ChatType.PRIVATE)],
    states={BROADCAST_BASIC_MEMBERS: [MessageHandler(~filters.COMMAND, broadcast_basic_members)]},
    fallbacks=[
        CommandHandler('cancel_broadcast', cancel_broadcast_basic_members),
        CommandHandler('cancel', cancel_broadcast_basic_members),
    ],
)


async def do_broadcast_course(update: Update, context: ContextTypes.DEFAULT_TYPE, course_id: int,
                              reply_markup: InlineKeyboardMarkup = None) -> int:
    logging.info(f"do_broadcast_course for {constants.id_to_course[course_id]} triggered by "
                 f"{helpers.repr_user_from_update(update)}")
    with Session(models.engine) as session:
        course_enrollments = session.query(models.Enrollment.tg_id).filter(
            models.Enrollment.course_id == course_id).all()
        tg_ids = [tg_id for (tg_id,) in course_enrollments]
        logging.info(f"got {len(tg_ids)} users from db for {constants.id_to_course[course_id]} broadcast")

    successful_count = 0
    failed_ids = []
    msg = update.message
    signature = f"\n\n---\n@{helpers.get_user(update).username} для курса {constants.id_to_course[course_id]}"

    for tg_id in tg_ids:
        if (successful_count + len(failed_ids)) % 50 == 0:
            logging.info(f"Course broadcast in progress: {successful_count} successful, "
                         f"{len(failed_ids)} failed so far")
        try:
            if msg.photo:
                await context.bot.send_photo(
                    chat_id=tg_id,
                    photo=msg.photo[-1].file_id,
                    caption=(msg.caption or "") + signature,
                    caption_entities=msg.caption_entities,
                    reply_markup=reply_markup
                )
            else:
                await context.bot.send_message(
                    chat_id=tg_id,
                    text=(msg.text or "") + signature,
                    entities=msg.entities,
                    reply_markup=reply_markup
                )
            successful_count += 1
        except Exception as e:
            failed_ids.append(tg_id)

    logging.info(f"Successfully {constants.id_to_course[course_id]} broadcast to {successful_count} users, "
                 f"failed {len(failed_ids)} users.")

    success_ids = list(set(tg_ids) - set(failed_ids))
    await update_users_in_db.update_users_after_broadcast(success_ids, failed_ids)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Successfully {constants.id_to_course[course_id]} broadcast to {successful_count} users, "
             f"failed {len(failed_ids)} users."
    )
    return ConversationHandler.END


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

SELECT_COURSE_TO_BROADCAST, COURSE_BROADCAST = range(2)


def get_active_courses_for_curator(update: Update) -> list[models.Course]:
    with Session(models.engine) as session:
        if is_admin_id(helpers.get_user(update).id):
            courses = session.query(models.Course).filter(
                    models.Course.is_active.is_(True)).all()
            logging.info(f"returning all the active courses for admin: {', '.join([course.name for course in courses])}")
        else:
            courses = session.query(models.Course).filter(
                    models.Course.curator_tg_id == str(helpers.get_user(update).id),
                    models.Course.is_active.is_(True)).all()
            logging.info(f"returning the active courses for curator: {', '.join([course.name for course in courses])}")
    return courses


async def start_course_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"start_course_broadcast handler triggered by {helpers.repr_user_from_update(update)}")

    courses = get_active_courses_for_curator(update)
    if not courses:
        await update.message.reply_text("Нет активных курсов, для которых ты куратор. Если они должны быть, напиши "
                                        "@lenka_colenka!")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(course.name, callback_data=f"broadcast_to_course:{course.id}")]
        for course in courses
    ]

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Выбери курс, для которого сделать рассылку:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return SELECT_COURSE_TO_BROADCAST


async def select_course(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    logging.info(f"select_course handler triggered by {helpers.repr_user_from_update(update)}")

    course_id = int(update.callback_query.data.split(":")[1])
    context.user_data["broadcast_to_course"] = course_id

    await update.callback_query.edit_message_text(
        text=f"Пришли сообщение, чтобы отправить всем пользователям в потоке {constants.id_to_course[course_id]}"
    )
    return COURSE_BROADCAST


@is_curator_for_course_in_context
async def course_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await do_broadcast_course(update, context, context.user_data["broadcast_to_course"])
    clear_state(context)
    return ConversationHandler.END


course_broadcast_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("course_broadcast", start_course_broadcast, filters.ChatType.PRIVATE)
    ],
    states={
        SELECT_COURSE_TO_BROADCAST: [CallbackQueryHandler(select_course, pattern=r"^broadcast_to_course:\d+$")],
        COURSE_BROADCAST: [
            MessageHandler(~filters.COMMAND, course_broadcast),
            CommandHandler("course_broadcast", start_course_broadcast, filters.ChatType.PRIVATE),
        ]
    },
    fallbacks=[
        CommandHandler('cancel_broadcast', cancel_broadcast),
        CommandHandler("cancel", cancel_broadcast),
    ],
    name="course_broadcast_conversation",
    persistent=True
)


def clear_state(context: ContextTypes.DEFAULT_TYPE) -> None:
    if "broadcast_to_course" in context.user_data:
        del context.user_data["broadcast_to_course"]


GET_COURSE_USERS = 1


async def start_course_get_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"start_course_get_users handler triggered by {helpers.repr_user_from_update(update)}")

    courses = get_active_courses_for_curator(update)
    if not courses:
        await update.message.reply_text("Нет активных курсов, для которых ты куратор. Если они должны быть, напиши "
                                        "@lenka_colenka!")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(course.name, callback_data=f"course_get_users:{course.id}")]
        for course in courses
    ]

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Выбери курс, для которого узнать число подписчиков:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return GET_COURSE_USERS


# todo: maybe add check that caller is a curator for course in query callback?
async def course_get_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    logging.info(f"course_get_users handler triggered by {helpers.repr_user_from_update(update)}")

    course_id = int(update.callback_query.data.split(":")[1])

    with Session(models.engine) as session:
        course_users_count = session.query(models.Enrollment).filter(models.Enrollment.course_id == course_id).count()

    await update.callback_query.edit_message_text(
        text=f"{course_users_count} пользователей подписались на {constants.id_to_course[course_id]}"
    )
    return ConversationHandler.END


async def cancel_get_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"cancel_get_users handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="course get users cancelled",
    )
    return ConversationHandler.END


course_get_users_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("course_get_users", start_course_get_users, filters.ChatType.PRIVATE)
    ],
    states={
        GET_COURSE_USERS: [
            CallbackQueryHandler(course_get_users, pattern=r"^course_get_users:\d+$"),
            CommandHandler("course_get_users", start_course_get_users, filters.ChatType.PRIVATE)
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel_get_users),
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


@is_curator(constants.dmls_course_id)
async def dmls_notification_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"dmls_notification_on handler triggered by {helpers.repr_user_from_update(update)}")
    models.dmls_notification_on = True

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="DMLS notification is ON" if models.dmls_notification_on else "DMLS notification is OFF"
    )


@is_curator(constants.dmls_course_id)
async def dmls_notification_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"dmls_notification_off handler triggered by {helpers.repr_user_from_update(update)}")
    models.dmls_notification_on = False

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="DMLS notification is ON" if models.dmls_notification_on else "DMLS notification is OFF"
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
    silent = False

    if len(args) not in (2, 3):
        await update.message.reply_text("Usage: /add_days <username> <number> [-silent]")
        return

    if len(args) == 3:
        if args[2] == "-silent":
            silent = True
        else:
            await update.message.reply_text(
                f"Unknown option: {args[2]}\nUsage: /add_days <username> <number> [-silent]")
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

    if not silent:
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
    logging.info(f"{username} has {membership_info.get_overall_level().name} subscription")

    with (Session(models.engine) as session):
        result = session \
            .query(models.Course)\
            .join(models.Enrollment, models.Enrollment.course_id == models.Course.id)\
            .filter(models.Enrollment.tg_id == tg_id).all()

    courses = sorted([(course.id, course.name, 'active' if course.is_active else 'inactive') for course in result])
    courses = [f"{course[0]}, {course[1]}, {course[2]}" for course in courses]

    logging.info(f"{username} is subscribed to {' '.join([str(x) for x in courses])}")

    courses_str = "\n - ".join(courses)
    await update.message.reply_text(
        f"<b>{username} has {membership_info.get_overall_level().name} subscription:</b>\n\n{membership_info}\n\n"
        f"<b>{username} is subscribed to</b>\n - {courses_str}",
        parse_mode="HTML")
