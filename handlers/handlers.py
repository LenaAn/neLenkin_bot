import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

import constants
import helpers


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


async def handle_mock_leetcode(update: Update) -> None:
    logging.info(f"mock_leetcode triggered by {helpers.get_user(update)}")
    # todo:
    # if user is enrolled, show "Перестать получать уведомления", otherwise show "Хочу получать уведомления!"
    button_list = [
        InlineKeyboardButton("Хочу участвовать!", callback_data="leetcode_enroll"),
        InlineKeyboardButton("Назад", callback_data="back"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    await update.callback_query.edit_message_text(
        text=constants.mock_leetcode_description,
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML")


async def handle_leetcode_enroll(update: Update) -> None:
    logging.info(f"leetcode_enroll handled by {helpers.get_user(update)}")
    button_list = [
        InlineKeyboardButton("Я передумала, отписаться", callback_data="leetcode_unenroll"),
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
    await handle_mock_leetcode(update)


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
