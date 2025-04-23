import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler

import settings
import constants

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def get_user(update: Update):
    if hasattr(update, "callback_query") and update.callback_query:
        return update.callback_query.from_user
    if hasattr(update, "message") and update.message:
        return update.message.from_user


def main_menu() -> InlineKeyboardMarkup:
    button_list = [
        InlineKeyboardButton("Как вступить?", callback_data="how_to_join"),
        InlineKeyboardButton("Хочу читать Кабанчика!", callback_data="ddia"),
        InlineKeyboardButton("Хочу читать SRE Book!", callback_data="sre_book"),
        InlineKeyboardButton("LeetCode мок-собеседования!", callback_data="mock_leetcode")
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    return InlineKeyboardMarkup(menu)


def back_menu() -> InlineKeyboardMarkup:
    button_list = [
        InlineKeyboardButton("Назад", callback_data="back"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    return InlineKeyboardMarkup(menu)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"start triggered by {get_user(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=constants.club_description,
        reply_markup=main_menu()
    )


async def handle_back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"back_to_start triggered by {get_user(update)}")
    await update.callback_query.edit_message_text(
        text=constants.club_description,
        reply_markup=main_menu()
    )


async def handle_how_to_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"how_to_join triggered by {get_user(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=constants.how_to_join_description,
        reply_markup=back_menu())
    return


async def handle_ddia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"ddia triggered by {get_user(update)}")
    button_list = [
        InlineKeyboardButton("Хочу сделать презентацию!", callback_data="how_to_present"),
        InlineKeyboardButton("Назад", callback_data="back"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=constants.ddia_description,
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML")
    return


async def handle_back_to_ddia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"back_to_ddia triggered by {get_user(update)}")
    await handle_ddia(update, context)


async def handle_sre_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"sre_book triggered by {get_user(update)}")
    button_list = [
        InlineKeyboardButton("Назад", callback_data="back"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=constants.sre_book_description,
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML")
    return


async def handle_mock_leetcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"mock_leetcode triggered by {get_user(update)}")
    button_list = [
        InlineKeyboardButton("Назад", callback_data="back"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=constants.mock_leetcode_description,
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML")
    return


async def handle_how_to_present(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"how_to_present triggered by {get_user(update)}")
    button_list = [
        InlineKeyboardButton("Назад", callback_data="back_to_ddia"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=constants.how_to_present_description,
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML")
    return


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    handlers = {
        "back": handle_back_to_start,
        "how_to_join": handle_how_to_join,
        "ddia": handle_ddia,
        "back_to_ddia": handle_back_to_ddia,
        "sre_book": handle_sre_book,
        "mock_leetcode": handle_mock_leetcode,
        "how_to_present": handle_how_to_present,
    }

    handler = handlers.get(query.data)
    if handler:
        await handler(update, context)
    else:
        logging.warning(f"Unhandled callback query data: {query.data}")


async def command_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"help triggered by {get_user(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Бот находится в стадии разработки, пожалуйста не ломайте его 🥺.\n"
             "Если бот плохо себя ведет, пожалуйста напишите Ленке @lenka_colenka.\n\n"
             "Поддерживаемые команды:\n"
             "/start — Главное меню\n"
             "/help — Справка"
    )


async def private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"private message handler triggered by {get_user(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Я не понимаю сообщения, только эти две команды:\n"
             "/start — Главное меню\n"
             "/help — Справка"
    )


if __name__ == '__main__':
    application = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', command_help))
    application.add_handler(MessageHandler(~filters.COMMAND, private_message))

    application.add_handler(CallbackQueryHandler(button_click))

    application.run_polling()
