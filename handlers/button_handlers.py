import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import constants
from courses import course_handlers
import helpers
from membership import boosty_handlers, patreon_handlers
import settings


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    handlers_dict = {
        "back": handle_back_to_start,
        "how_to_join": handle_how_to_join,
        "course_info": course_handlers.handle_course_info,
        "back_to_ddia": handle_back_to_ddia,
        "enroll": course_handlers.handle_enroll,
        "unenroll": course_handlers.handle_unenroll,
        "how_to_present": handle_how_to_present,
        "disconnect_patreon": patreon_handlers.disconnect_patreon_handler,
        "disconnect_boosty": boosty_handlers.disconnect_boosty_handler,
    }

    command: str = query.data
    if ":" in query.data:
        context.user_data["callback_course_id"] = int(query.data.split(":")[1])
        command = query.data.split(":")[0]

    handler = handlers_dict.get(command)
    if handler:
        await handler(update, context)
    else:
        logging.warning(f"Unhandled callback query data: {command} by {helpers.repr_user_from_update(update)}")


async def handle_back_to_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"back_to_start triggered by {helpers.repr_user_from_update(update)}")
    await update.callback_query.edit_message_text(
        text=constants.club_description,
        reply_markup=helpers.main_menu()
    )


async def handle_how_to_join(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"how_to_join triggered by {helpers.repr_user_from_update(update)}")
    await update.callback_query.edit_message_text(
        text=constants.how_to_join_description,
        reply_markup=helpers.join_menu())


async def handle_back_to_ddia(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"back_to_ddia triggered by {helpers.repr_user_from_update(update)}")
    await course_handlers.handle_course_info(update, constants.ddia_4_course_id)


async def handle_how_to_present(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
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
        logging.info(f"error with invalid update")
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
