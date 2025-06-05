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
        "mock_leetcode": handle_mock_leetcode,
        "how_to_present": handle_how_to_present,
        "leetcode_enroll": handle_leetcode_enroll,
        "leetcode_unenroll": handle_leetcode_unenroll,
    }

    handler = handlers_dict.get(query.data)
    if handler:
        await handler(update)
    else:
        logging.warning(f"Unhandled callback query data: {query.data}")


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


async def handle_sre_book(update: Update) -> None:
    logging.info(f"sre_book triggered by {helpers.get_user(update)}")
    button_list = [
        InlineKeyboardButton("Назад", callback_data="back"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    await update.callback_query.edit_message_text(
        text=constants.sre_book_description,
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML")


def user_is_enrolled_in_leetcode(tg_user: User) -> bool:
    with Session(models.engine) as session:
        users_exists = session.scalar(
            select(exists().where((models.Enrollment.tg_id == str(tg_user.id)) & (models.Enrollment.course_id == 7)))
        )
    if users_exists:
        logging.info(f"user is already enrolled in Leetcode Mocks: {tg_user}")
    else:
        logging.info(f"user is not already enrolled in Leetcode Mocks: {tg_user}")
    return users_exists


async def handle_mock_leetcode(update: Update) -> None:
    tg_user = helpers.get_user(update)
    logging.info(f"mock_leetcode triggered by {tg_user}")

    if user_is_enrolled_in_leetcode(tg_user):
        button_list = [
            InlineKeyboardButton("Перестать получать уведомления", callback_data="leetcode_unenroll"),
            InlineKeyboardButton("Назад", callback_data="back"),
        ]
        menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
        await update.callback_query.edit_message_text(
            text=constants.mock_leetcode_description + "\n\n" + constants.leetcode_enroll_description,
            reply_markup=InlineKeyboardMarkup(menu),
            parse_mode="HTML")
    else:
        button_list = [
            InlineKeyboardButton("Хочу участвовать!", callback_data="leetcode_enroll"),
            InlineKeyboardButton("Назад", callback_data="back"),
        ]
        menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
        await update.callback_query.edit_message_text(
            text=constants.mock_leetcode_description + "\n\n" + constants.leetcode_cta_description,
            reply_markup=InlineKeyboardMarkup(menu),
            parse_mode="HTML")


async def handle_leetcode_enroll(update: Update) -> None:
    tg_user = helpers.get_user(update)
    logging.info(f"leetcode_enroll handled by {tg_user}")

    with Session(models.engine) as session:
        enrollment = models.Enrollment(
            course_id=7,  # todo: dirty hard-code
            tg_id=tg_user.id
        )
        session.add(enrollment)
        try:
            session.commit()
            logging.info(f"Add user enrollment to Leetcode to db: {tg_user}")
        except IntegrityError as e:
            session.rollback()
            logging.info(f"Didn't add user {tg_user.username} enrollment to Leetcode to db: {e}")
        except Exception as e:
            session.rollback()
            logging.warning(f"Couldn't add user enrollment to Leetcode: {e}")
    button_list = [
        InlineKeyboardButton("Перестать получать уведомления", callback_data="leetcode_unenroll"),
        InlineKeyboardButton("Назад", callback_data="back"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    await update.callback_query.edit_message_text(
        text=constants.leetcode_enroll_description,
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML"
    )


async def handle_leetcode_unenroll(update: Update) -> None:
    logging.info(f"leetcode_unenroll handled by {helpers.get_user(update)}")
    # todo: actually delete user from enrollments table
    button_list = [
        InlineKeyboardButton("Назад", callback_data="back"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    await update.callback_query.edit_message_text(
        text=constants.leetcode_unenroll_description,
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML"
    )


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
