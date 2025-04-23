import logging
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler

import constants
import handlers
import helpers
import settings

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"start triggered by {helpers.get_user(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=constants.club_description,
        reply_markup=helpers.main_menu()
    )


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    handlers_dict = {
        "back": handlers.handle_back_to_start,
        "how_to_join": handlers.handle_how_to_join,
        "ddia": handlers.handle_ddia,
        "back_to_ddia": handlers.handle_back_to_ddia,
        "sre_book": handlers.handle_sre_book,
        "mock_leetcode": handlers.handle_mock_leetcode,
        "how_to_present": handlers.handle_how_to_present,
    }

    handler = handlers_dict.get(query.data)
    if handler:
        await handler(update)
    else:
        logging.warning(f"Unhandled callback query data: {query.data}")


async def command_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"help triggered by {helpers.get_user(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Бот находится в стадии разработки, пожалуйста не ломайте его 🥺.\n"
             "Если бот плохо себя ведет, пожалуйста напишите Ленке @lenka_colenka.\n\n"
             "Поддерживаемые команды:\n"
             "/start — Главное меню\n"
             "/help — Справка"
    )


async def private_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"private message handler triggered by {helpers.get_user(update)}")
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
