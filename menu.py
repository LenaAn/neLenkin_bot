import logging
from telegram import Update
from telegram.ext import ContextTypes

import constants
import helpers


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"start triggered by {helpers.get_user(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=constants.club_description,
        reply_markup=helpers.main_menu()
    )


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
