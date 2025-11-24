import datetime
import logging

from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, User
from telegram.ext import ContextTypes

import constants
import helpers
import membership
import models
from handlers import patreon_handlers
import settings


async def button_click(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    # todo: refactor so enrolling new course doesn't involve writing new code
    handlers_dict = {
        "back": handle_back_to_start,
        "how_to_join": handle_how_to_join,
        "ddia": handle_ddia,
        "back_to_ddia": handle_back_to_ddia,
        "ddia_enroll": handle_ddia_enroll,
        "ddia_unenroll": handle_ddia_unenroll,
        "mock_leetcode": handle_mock_leetcode,
        "leetcode_grind": handle_leetcode_grind,
        "leetcode_grind_enroll": handle_leetcode_grind_enroll,
        "leetcode_grind_unenroll": handle_leetcode_grind_unenroll,
        "how_to_present": handle_how_to_present,
        "leetcode_enroll": handle_leetcode_enroll,
        "leetcode_unenroll": handle_leetcode_unenroll,
        "codecrafters": handle_codecrafters,
        "codecrafters_enroll": handle_codecrafters_enroll,
        "codecrafters_unenroll": handle_codecrafters_unenroll,
        "membership": handle_membership,
        "disconnect_patreon": patreon_handlers.disconnect_patreon_handler,
    }

    handler = handlers_dict.get(query.data)
    if handler:
        await handler(update)
    else:
        logging.warning(f"Unhandled callback query data: {query.data} by {helpers.repr_user_from_update(update)}")


async def handle_back_to_start(update: Update) -> None:
    logging.info(f"back_to_start triggered by {helpers.repr_user_from_update(update)}")
    await update.callback_query.edit_message_text(
        text=constants.club_description,
        reply_markup=helpers.main_menu()
    )


async def handle_how_to_join(update: Update) -> None:
    logging.info(f"how_to_join triggered by {helpers.repr_user_from_update(update)}")
    await update.callback_query.edit_message_text(
        text=constants.how_to_join_description,
        reply_markup=helpers.join_menu())


async def handle_ddia(update: Update) -> None:
    logging.info(f"ddia triggered by {helpers.repr_user_from_update(update)}")
    await handle_course_info(update, constants.ddia_4_course_id, constants.ddia_description,
                             constants.ddia_enroll_description, constants.ddia_cta_description,
                             "ddia_enroll", "ddia_unenroll")


async def handle_back_to_ddia(update: Update) -> None:
    logging.info(f"back_to_ddia triggered by {helpers.repr_user_from_update(update)}")
    await handle_ddia(update)


def user_is_enrolled(tg_user: User, course_id: int) -> bool:
    with Session(models.engine) as session:
        users_exists = session.scalar(
            select(exists().where(
                (models.Enrollment.tg_id == str(tg_user.id)) & (models.Enrollment.course_id == course_id))
            )
        )
    if users_exists:
        logging.info(f"user is already enrolled in {constants.id_to_course[course_id]}: {helpers.repr_user(tg_user)}")
    else:
        logging.info(
            f"user is not already enrolled in {constants.id_to_course[course_id]}: {helpers.repr_user(tg_user)}")
    return users_exists


async def handle_course_info(update: Update, course_id: int, course_description: str, enroll_description: str,
                             cta_description: str, enroll_callback: str, unenroll_callback: str) -> None:
    logging.info(f"handle_course_info for {constants.id_to_course[course_id]} triggered by "
                 f"{helpers.repr_user_from_update(update)}")

    tg_user = helpers.get_user(update)
    if user_is_enrolled(tg_user, course_id):
        button_list = [
            InlineKeyboardButton("Перестать получать уведомления", callback_data=unenroll_callback),
            InlineKeyboardButton("Назад", callback_data="back"),
        ]
        menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
        await update.callback_query.edit_message_text(
            text=course_description + "\n\n" + enroll_description,
            reply_markup=InlineKeyboardMarkup(menu),
            parse_mode="HTML")
    else:
        button_list = [
            InlineKeyboardButton("Хочу участвовать!", callback_data=enroll_callback),
            InlineKeyboardButton("Назад", callback_data="back"),
        ]
        menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
        await update.callback_query.edit_message_text(
            text=course_description + "\n\n" + cta_description,
            reply_markup=InlineKeyboardMarkup(menu),
            parse_mode="HTML")


async def handle_mock_leetcode(update: Update) -> None:
    await handle_course_info(update, constants.leetcode_course_id, constants.mock_leetcode_description,
                             constants.leetcode_enroll_description, constants.leetcode_cta_description,
                             "leetcode_enroll", "leetcode_unenroll")


async def handle_leetcode_grind(update: Update) -> None:
    await handle_course_info(update, constants.grind_course_id, constants.leetcode_grind_description,
                             constants.leetcode_grind_enroll_description, constants.leetcode_grind_cta_description,
                             "leetcode_grind_enroll", "leetcode_grind_unenroll")


async def handle_codecrafters(update: Update) -> None:
    await handle_course_info(update, constants.codecrafters_course_id, constants.codecrafters_description,
                             constants.codecrafters_enroll_description, constants.codecrafters_cta_description,
                             "codecrafters_enroll", "codecrafters_unenroll")


async def reply_for_patreon_members(update: Update, membership_info) -> None:
    # todo: here a button to Отвязать профиль Patreon
    logging.info(f"reply_for_patreon_members triggered by {helpers.get_user(update)}")

    msg: str = membership_info.get_overall_level().description
    msg += (f"\n\nПривязанный профиль Patreon: {membership_info.patreon_email}. Ты донатишь "
            f"${membership_info.patreon_currently_entitled_amount_cents // 100}. Спасибо! ❤️")

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("Отвязать профиль Patreon", callback_data="disconnect_patreon"),
    ]])

    await update.callback_query.edit_message_text(
        text=msg,
        reply_markup=reply_markup,
    )


async def reply_for_activity_members(update: Update, membership_info) -> None:
    logging.info(f"reply_for_activity_members triggered by {helpers.get_user(update)}")

    msg: str = membership_info.get_overall_level().description
    if not membership_info.member_level_by_activity_expiration:
        msg += f"\n\nУ тебя вечная подписка за активное участие в клубе!"
    else:
        if membership_info.member_level_by_activity_expiration < datetime.date.today():
            msg += f"\n\nТвоя подписка за активное участие закончилась :("
        else:
            msg += (f"\n\nТвоя подписка за активное участие истечет "
                    f"{membership_info.member_level_by_activity_expiration}."
                    f"\n\nЧтобы сохранить 💜Pro подписку, сделай презентацию либо подпишись на "
                    f"<a href='https://www.patreon.com/c/LenaAnyusha'>Patreon</a> хотя бы на $15 в месяц.\n\n")

    if membership_info.patreon_email != "":
        reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("Отвязать профиль Patreon", callback_data="disconnect_patreon"),
        ]])
    else:
        reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("Привязать профиль Patreon", callback_data="connect_patreon"),
        ]])

    await update.callback_query.edit_message_text(
        text=msg,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )


async def reply_for_basic_with_linked_patreon(update: Update, membership_info) -> None:
    logging.info(f"reply_for_basic_with_linked_patreon triggered by {helpers.get_user(update)}")

    msg: str = membership_info.get_overall_level().description
    msg += f"\n\nПривязанный профиль Patreon: {membership_info.patreon_email}."
    if membership_info.patreon_currently_entitled_amount_cents > 0:
        msg += f" Ты донатишь ${membership_info.patreon_currently_entitled_amount_cents // 100}. Спасибо! ❤️"
    else:
        msg += f" Ты не донатишь мне на Patreon️"
    msg += ("\n\nЧтобы улучшить подписку, сделай презентацию либо подпишись на "
            "<a href='https://www.patreon.com/c/LenaAnyusha'>Patreon</a> хотя бы на $15 в месяц")

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("Отвязать профиль Patreon", callback_data="disconnect_patreon"),
    ]])
    await update.callback_query.edit_message_text(
        text=msg,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )


async def reply_for_basic(update: Update, membership_info) -> None:
    logging.info(f"reply_for_basic triggered by {helpers.get_user(update)}")

    msg: str = membership_info.get_overall_level().description
    msg += ("\n\nЧтобы улучшить подписку, сделай презентацию либо подпишись на "
            "<a href='https://www.patreon.com/c/LenaAnyusha'>Patreon</a> хотя бы на $15 в месяц")
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("Привязать профиль Patreon", callback_data="connect_patreon"),
    ]])
    await update.callback_query.edit_message_text(
        text=msg,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )


async def handle_membership(update: Update) -> None:
    tg_user = helpers.get_user(update)
    logging.info(f"handle_membership triggered by {tg_user}")

    membership_info = membership.get_user_membership_info(tg_user.id, tg_user.username)

    if membership_info.get_patreon_level() == membership.pro:
        await reply_for_patreon_members(update, membership_info)
        return

    if membership_info.member_level_by_activity == membership.pro:
        await reply_for_activity_members(update, membership_info)
        return

    # otherwise user has basic level
    if membership_info.patreon_email != "":
        await reply_for_basic_with_linked_patreon(update, membership_info)
        return

    # user has a basic subscription: no Redis donation, no activity membership
    # and also no Patreon linked
    await reply_for_basic(update, membership_info)
    return


async def handle_enroll(update: Update, course_id: int, unenroll_callback_data: str, enroll_description: str) -> None:
    logging.info(f"enroll for {constants.id_to_course[course_id]} handled by {helpers.repr_user_from_update(update)}")

    tg_user = helpers.get_user(update)
    with Session(models.engine) as session:
        enrollment = models.Enrollment(
            course_id=course_id,
            tg_id=tg_user.id
        )
        session.add(enrollment)
        try:
            session.commit()
            logging.info(f"Add user enrollment to {constants.id_to_course[course_id]} to db: "
                         f"{helpers.repr_user(tg_user)}")
        except IntegrityError as e:
            session.rollback()
            logging.info(f"Didn't add user {helpers.repr_user(tg_user)} enrollment to "
                         f"{constants.id_to_course[course_id]} to db: {e}")
        except Exception as e:
            session.rollback()
            logging.warning(f"Couldn't add user enrollment to {constants.id_to_course[course_id]}: {e}")
    button_list = [
        InlineKeyboardButton("Перестать получать уведомления", callback_data=unenroll_callback_data),
        InlineKeyboardButton("Назад", callback_data="back"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    await update.callback_query.edit_message_text(
        text=enroll_description,
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML"
    )


async def handle_unenroll(update: Update, course_id: int, unenroll_description: str) -> None:
    logging.info(f"unenroll for {constants.id_to_course[course_id]} handled by {helpers.repr_user_from_update(update)}")

    tg_user = helpers.get_user(update)
    with Session(models.engine) as session:
        try:
            session.query(models.Enrollment).filter(
                (models.Enrollment.tg_id == str(tg_user.id)) & (models.Enrollment.course_id == course_id)).delete()
            session.commit()
            logging.info(f"Deleted user enrollment to {constants.id_to_course[course_id]} from db: "
                         f"{helpers.repr_user(tg_user)}")
        except Exception as e:
            session.rollback()
            logging.error(f"Couldn't delete user enrollment to {constants.id_to_course[course_id]}: {e}")
            raise e  # to propagate it to error handler

    button_list = [
        InlineKeyboardButton("Назад", callback_data="back"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    await update.callback_query.edit_message_text(
        text=unenroll_description,
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML"
    )


async def handle_leetcode_enroll(update: Update) -> None:
    await handle_enroll(
        update,
        constants.leetcode_course_id,
        "leetcode_unenroll",
        constants.leetcode_enroll_description)


async def handle_leetcode_unenroll(update: Update) -> None:
    await handle_unenroll(update, constants.leetcode_course_id, constants.leetcode_unenroll_description)


async def handle_leetcode_grind_enroll(update: Update) -> None:
    await handle_enroll(
        update,
        constants.grind_course_id,
        "leetcode_grind_unenroll",
        constants.leetcode_grind_enroll_description)


async def handle_leetcode_grind_unenroll(update: Update) -> None:
    await handle_unenroll(update, constants.grind_course_id, constants.leetcode_grind_unenroll_description)


async def handle_codecrafters_enroll(update: Update) -> None:
    await handle_enroll(
        update,
        constants.codecrafters_course_id,
        "codecrafters_unenroll",
        constants.codecrafters_enroll_description)


async def handle_codecrafters_unenroll(update: Update) -> None:
    await handle_unenroll(update, constants.codecrafters_course_id, constants.codecrafters_unenroll_description)


async def handle_ddia_enroll(update: Update) -> None:
    await handle_enroll(
        update,
        constants.ddia_4_course_id,
        "ddia_unenroll",
        constants.ddia_enroll_description)


async def handle_ddia_unenroll(update: Update) -> None:
    await handle_unenroll(update, constants.ddia_4_course_id, constants.ddia_unenroll_description)


async def handle_how_to_present(update: Update) -> None:
    logging.info(f"how_to_present triggered by {helpers.repr_user_from_update(update)}")
    button_list = [
        InlineKeyboardButton("Назад", callback_data="back_to_ddia"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    await update.callback_query.edit_message_text(
        text=constants.how_to_present_description,
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    # todo: ignore "Message is not modified" and "Query is too old" errors?
    if not isinstance(update, Update):
        logging.info(f"error with invalid update", exc_info=context.error)
    else:
        logging.info(f"error triggered by {update}", exc_info=context.error)
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=constants.error_description,
                parse_mode="HTML")
        except Exception as e:
            logging.info(f"couldn't send error message to user", exc_info=e)

        try:
            await context.bot.send_message(
                chat_id=settings.ADMIN_CHAT_ID,
                text=f"error triggered by {helpers.get_user(update)}: {context.error}",
                parse_mode="HTML")
        except Exception as e:
            logging.error(f"couldn't send error message to admin", exc_info=e)
