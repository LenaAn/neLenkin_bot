import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler
from typing import Union, List

import settings

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def main_menu() -> InlineKeyboardMarkup:
    button_list = [
        InlineKeyboardButton("Как вступить?", callback_data="how_to_join"),
        InlineKeyboardButton("Хочу читать Кабанчика!", callback_data="ddia"),
        InlineKeyboardButton("Хочу читать SRE Book!", callback_data="sre_book")
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
    club_description = \
        ("(не)Ленкин клуб @lenka_ne_club — это клуб для тех, кто хочет становиться лучше как системный "
         "(инфраструктурный) программист (в противовес продуктовой разработке). \n\n"
         "Обсуждаем распределенные системы, базы данных, data streaming и все, что рядом находится. Фокус — прикладные "
         "знания, которые помогут в работе.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=club_description, reply_markup=main_menu())


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    if query.data == "back":
        await start(update, context)
        return

    if query.data == "how_to_join":
        response_text = ("Просто вступить в группу и написать интро про себя с хэштегом #whois — чем занимаешься, где "
                         "работаешь или учишься, где живешь, в какой активности хочешь участвовать в клубе.\n\n"
                         "Клуб держится на доверии и активном участии членов клуба. Когда ты пишешь содержательное "
                         "интро о себе, ты даешь возможность другим членам клуба задать тебе вопрос / попросить совета "
                         "/ позвать на сходку.\n\n"
                         "Интро уже состоящих в клубе людей ты можешь найти по хэштегу #whois. \n\n"
                         "Вступить ➡️ @lenka_ne_club")
    elif query.data == "row2_action":
        response_text = "You clicked Row 2!"
    else:
        response_text = "Unknown action."

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=response_text,
        reply_markup=back_menu())


async def command_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Бот находится в стадии разработки, пожалуйста не ломайте его 🥺.\n"
             "Если бот плохо себя ведет, пожалуйста напишите Ленке @lenka_colenka.\n\n"
             "Поддерживаемые команды:\n"
             "/start — Главное меню\n"
             "/help — Справка"
    )


async def private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Private message handler triggered")
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
