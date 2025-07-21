import logging

from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, User
from telegram.ext import ContextTypes

import constants
import helpers
import models
import settings


async def button_click(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    handlers_dict = {
        "back": handle_back_to_start,
        "how_to_join": handle_how_to_join,
        "ddia": handle_ddia,
        "back_to_ddia": handle_back_to_ddia,
        "sre_book": handle_sre_book,
        "sre_enroll": handle_sre_enroll,
        "sre_unenroll": handle_sre_unenroll,
        "mock_leetcode": handle_mock_leetcode,
        "how_to_present": handle_how_to_present,
        "leetcode_enroll": handle_leetcode_enroll,
        "leetcode_unenroll": handle_leetcode_unenroll,
    }

    handler = handlers_dict.get(query.data)
    if handler:
        await handler(update)
    else:
        logging.warning(f"Unhandled callback query data: {query.data} by {helpers.get_user(update)}")


async def handle_back_to_start(update: Update) -> None:
    logging.info(f"back_to_start triggered by {helpers.get_user(update)}")
    await update.callback_query.edit_message_text(
        text=constants.club_description,
        reply_markup=helpers.main_menu()
    )


async def handle_how_to_join(update: Update) -> None:
    logging.info(f"how_to_join triggered by {helpers.get_user(update)}")
    await update.callback_query.edit_message_text(
        text=constants.how_to_join_description,
        reply_markup=helpers.join_menu())


async def handle_ddia(update: Update) -> None:
    logging.info(f"ddia triggered by {helpers.get_user(update)}")
    button_list = [
        InlineKeyboardButton("Хочу сделать презентацию!", callback_data="how_to_present"),
        InlineKeyboardButton("Назад", callback_data="back"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    await update.callback_query.edit_message_text(
        text=constants.ddia_description,
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML")


async def handle_back_to_ddia(update: Update) -> None:
    logging.info(f"back_to_ddia triggered by {helpers.get_user(update)}")
    await handle_ddia(update)


def user_is_enrolled(tg_user: User, course_id: int) -> bool:
    with Session(models.engine) as session:
        users_exists = session.scalar(
            select(exists().where(
                (models.Enrollment.tg_id == str(tg_user.id)) & (models.Enrollment.course_id == course_id))
            )
        )
    if users_exists:
        logging.info(f"user is already enrolled in {constants.id_to_course[course_id]}: {tg_user}")
    else:
        logging.info(f"user is not already enrolled in {constants.id_to_course[course_id]}: {tg_user}")
    return users_exists


async def handle_course_info(update: Update, course_id: int, course_description: str, enroll_description: str,
                             cta_description: str, enroll_callback: str, unenroll_callback: str) -> None:
    tg_user = helpers.get_user(update)
    logging.info(f"handle_course_info for {constants.id_to_course[course_id]} triggered by {tg_user}")

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


async def handle_sre_book(update: Update) -> None:
    await handle_course_info(update, constants.sre_course_id, constants.sre_book_description,
                             constants.sre_enroll_description, constants.sre_book_cta_description,
                             "sre_enroll", "sre_unenroll")


async def handle_enroll(update: Update, course_id: int, unenroll_callback_data: str, enroll_description: str) -> None:
    tg_user = helpers.get_user(update)
    logging.info(f"enroll for {constants.id_to_course[course_id]} handled by {tg_user}")

    with Session(models.engine) as session:
        enrollment = models.Enrollment(
            course_id=course_id,
            tg_id=tg_user.id
        )
        session.add(enrollment)
        try:
            session.commit()
            logging.info(f"Add user enrollment to {constants.id_to_course[course_id]} to db: {tg_user}")
        except IntegrityError as e:
            session.rollback()
            logging.info(
                f"Didn't add user {tg_user.username} enrollment to {constants.id_to_course[course_id]} to db: {e}")
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
    tg_user = helpers.get_user(update)
    logging.info(f"unenroll for {constants.id_to_course[course_id]} handled by {tg_user}")

    with Session(models.engine) as session:
        try:
            session.query(models.Enrollment).filter(
                (models.Enrollment.tg_id == str(tg_user.id)) & (models.Enrollment.course_id == course_id)).delete()
            session.commit()
            logging.info(f"Deleted user enrollment to {constants.id_to_course[course_id]} from db: {tg_user}")
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


async def handle_sre_enroll(update: Update) -> None:
    await handle_enroll(
        update,
        constants.sre_course_id,
        "sre_unenroll",
        constants.sre_enroll_description)


async def handle_sre_unenroll(update: Update) -> None:
    await handle_unenroll(update, constants.sre_course_id, constants.sre_unenroll_description)


async def handle_how_to_present(update: Update) -> None:
    logging.info(f"how_to_present triggered by {helpers.get_user(update)}")
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
        logging.info(f"error by not even update: {update}, exc_info=context.error")
    else:
        logging.info(f"error triggered by {helpers.get_user(update)}", exc_info=context.error)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=constants.error_description,
            parse_mode="HTML")

        await context.bot.send_message(
            chat_id=settings.ADMIN_CHAT_ID,
            text=f"error triggered by {helpers.get_user(update)}: {context.error}",
            parse_mode="HTML")
