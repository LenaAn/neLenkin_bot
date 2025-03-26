import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler
from typing import Union, List

import settings

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def build_menu(
        buttons: List[InlineKeyboardButton],
        n_cols: int,
        header_buttons: Union[InlineKeyboardButton, List[InlineKeyboardButton]] = None,
        footer_buttons: Union[InlineKeyboardButton, List[InlineKeyboardButton]] = None
) -> List[List[InlineKeyboardButton]]:
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons if isinstance(header_buttons, list) else [header_buttons])
    if footer_buttons:
        menu.append(footer_buttons if isinstance(footer_buttons, list) else [footer_buttons])
    return menu


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    button_list = [
        InlineKeyboardButton("Как вступить?", callback_data="how_to_add"),
        InlineKeyboardButton("Хочу читать Кабанчика!", callback_data="ddia"),
        InlineKeyboardButton("Хочу читать SRE Book!", callback_data="sre_book")
    ]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))

    club_description = \
        ("(не)Ленкин клуб @lenka_ne_club — это клуб для тех, кто хочет становиться лучше как системный "
         "(инфраструктурный) программист (в противовес продуктовой разработке). \n\n"
         "Обсуждаем распределенные системы, базы данных, data streaming и все, что рядом находится. Фокус — прикладные "
         "знания, которые помогут в работе.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=club_description, reply_markup=reply_markup)


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    if query.data == "col1_action":
        response_text = "You clicked Column 1!"
    elif query.data == "col2_action":
        response_text = "You clicked Column 2!"
    elif query.data == "row2_action":
        response_text = "You clicked Row 2!"
    else:
        response_text = "Unknown action."

    await context.bot.send_message(response_text)


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
