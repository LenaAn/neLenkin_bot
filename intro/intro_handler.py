import os
import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

import helpers


intro_logger = logging.getLogger(__name__)
intro_logger.setLevel(logging.INFO)


WAITING_INTRO = 1


how_to_join_description = \
    ("Привет! Рада что ты хочешь присоединиться к клубу!\n\n"
     "Напиши пожалуйста интро: чем занимаешься, где работаешь или учишься, на каком языке программируешь, "
     "какими технологиями интересуешься.\n\n"
     "Клуб держится на доверии и активном участии членов клуба. Когда ты пишешь содержательное "
     "интро о себе, ты даешь возможность другим членам клуба задать тебе вопрос / попросить совета "
     "/ позвать на сходку.\n\n"
     "Пример хорошего интро:\n"
     "<blockquote>Привет! Я Лена! Училась в СУНЦ МГУ, ФИВТ МФТИ, работала в Deutsche Bank, Google, Goldman Sachs, "
     "Redpanda, Confluent, сейчас занимаюсь этим клубом:)\n\n"
     "Живу в Белграде.\n\n"
     "На работе в основном работала с распределенными системами на C++ и Java (Kafka, Redpanda), но для души пишу на "
     "Python. Любимые технологии: Docker, Postres, FastAPI.\n\n"
     "Вот мой <a href='https://www.linkedin.com/in/elena-anyusheva'>линкедин</a> "
     "и <a href='https://t.me/lenka_ne_work'>телеграм-канал</a></blockquote>\n\n"
     "Интро пиши прямо в бота в ответ на это сообщение. Вызвать заново эту команду: /join, если передумала писать "
     "интро, вызови /cancel.")


async def start_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    intro_logger.info(f"start_join triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=how_to_join_description,
        parse_mode="HTML",
        disable_web_page_preview=True)
    return WAITING_INTRO


async def handle_intro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    intro_logger.info(f"handle_intro triggered by {helpers.repr_user_from_update(update)}: {update.message.text}")
    user = update.effective_user

    admin_chat_id = int(os.getenv('ADMIN_CHAT_ID'))

    await context.bot.forward_message(
        chat_id=admin_chat_id,
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id
    )

    await context.bot.send_message(
        chat_id=admin_chat_id,
        text=(
            f"👆 Intro above from:\n {user.username}" if user.username else f"ID: {user.id}"
        )
    )

    await update.message.reply_text("Спасибо! Админ просмотрит твое интро и свяжется с тобой! Мы стараемся отвечать за"
                                    " сутки")

    return ConversationHandler.END


async def cancel_intro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    intro_logger.info(f"cancel_intro handler triggered by {helpers.repr_user_from_update(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Отмена интро",
    )
    return ConversationHandler.END


intro_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("join", start_join, filters.ChatType.PRIVATE)],
    states={
        WAITING_INTRO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_intro),
            CommandHandler("join", start_join, filters.ChatType.PRIVATE)
        ],
    },
    fallbacks=[CommandHandler('cancel', cancel_intro)],
)
