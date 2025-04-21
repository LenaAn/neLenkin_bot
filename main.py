import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler

import settings

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
        logging.info(f"how_to_join triggered by {get_user(update)}")
        response_text = ("Просто вступить в группу и написать интро про себя с хэштегом #whois — чем занимаешься, где "
                         "работаешь или учишься, где живешь, в какой активности хочешь участвовать в клубе.\n\n"
                         "Клуб держится на доверии и активном участии членов клуба. Когда ты пишешь содержательное "
                         "интро о себе, ты даешь возможность другим членам клуба задать тебе вопрос / попросить совета "
                         "/ позвать на сходку.\n\n"
                         "Интро уже состоящих в клубе людей ты можешь найти по хэштегу #whois. \n\n"
                         "Вступить ➡️ @lenka_ne_club")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response_text,
            reply_markup=back_menu())
        return

    if query.data == "ddia":
        logging.info(f"ddia triggered by {get_user(update)}")
        response_text = (
            "Сейчас идет уже третий поток чтения \"книги с кабанчиком\" — Designing Data Intensive Applications. Третий "
            "поток начался 13-го марта 2025. Ты можешь начать читать не с начала, а с текущей главы. \n\n"
            "Чтобы узнать, какую главу обсуждаем на этой неделе, посмотри в "
            "<a href='https://docs.google.com/spreadsheets/d/1qsuaSn0ZkBmldY8hVnKWe41sSgaPG8ekd83csSUh5Qk/edit?gid=0#gid=0'>расписании</a>.\n\n"
            "Звонки проходят по четвергам в 18:00 по Берлину, неважно, летнее или зимнее время в Берлине. Вот "
            "<a href='https://us06web.zoom.us/j/81466072100?pwd=DfbheF4UTwJw23idId7KlQmYlQTJZj.1'>ссылка на звонок</a>,"
            " она не меняется. "
            "\n\nОбсуждение и координация происходят в <a href='t.me/lenka_ne_club/7209'>этом топике</a>.")
        button_list = [
            InlineKeyboardButton("Хочу сделать презентацию!", callback_data="how_to_present"),
            InlineKeyboardButton("Назад", callback_data="back"),
        ]
        menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response_text,
            reply_markup=InlineKeyboardMarkup(menu),
            parse_mode="HTML")
        return

    if query.data == "sre_book":
        logging.info(f"sre_book triggered by {get_user(update)}")
        response_text = (
            "⚠️SRE Book — это книга для тех, кто уже прочитал Кабанчика. Если ты еще не прочитала кабанчика, пожалуйста, "
            "не отвлекайся!! ⚠️\n\n"
            "SRE Book — книга про принципы и практики работы Site Reliability Engineer команды в Google.\n\n"
            "Ссылка на книгу <a href='https://sre.google/sre-book/table-of-contents/'>вот</a>. "
            "Созвоны по вторникам в 18:00 по Белграду (даже если часы перевели, мы ориентируемся на Белград).\n\n"
            "Вот <a href='https://docs.google.com/spreadsheets/d/1J15WCQyITeDZR64G9Ymf-pT_zSJm3m9Kvorp48ecy10/edit?gid=0#gid=0'>таблица с расписанием</a>, "
            "вот <a href='https://us06web.zoom.us/j/89699825499?pwd=252HFSD6l5TH2GYm7qDlI3QRahZNIZ.1'>ссылка на звонок</a>, "
            "вот <a href='t.me/lenka_ne_club/7272'>топик</a>.\n\n"
            "Пожалуйста записывайтесь с таблицу делать презентацию!")
        button_list = [
            InlineKeyboardButton("Назад", callback_data="back"),
        ]
        menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response_text,
            reply_markup=InlineKeyboardMarkup(menu),
            parse_mode="HTML")
        return

    if query.data == "mock_leetcode":
        logging.info(f"mock_leetcode triggered by {get_user(update)}")
        response_text = (
            "Прорешивать Leetcode — это хорошо, но на реальном собеседовании важно уметь рассказать ход решения, "
            "иногда на английском! В клубе мы практикуемся проходить собеседования в формате, приближенном к реальности.\n\n"
            "Каждый понедельник Лена объявляет тему этой недели. Желающие участвовать в мок-собеседованииях записываются "
            "в таблицу и в пятницу Лена объявляет пары. Два человека из пары созваниваются в удобное для них время "
            "(рассчитывай на полтора часа) и проводят мок-собеседование. Сначала первый партнер выступает в качестве "
            "интервьюера, а второй в качестве кандидата решает задачу. Потом партнеры меняются местами.\n\n"
            "Больше подробностей -- в закрепленном сообщении в чате!")
        button_list = [
            InlineKeyboardButton("Назад", callback_data="back"),
        ]
        menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response_text,
            reply_markup=InlineKeyboardMarkup(menu),
            parse_mode="HTML")
        return

    if query.data == "how_to_present":
        logging.info(f"how_to_present triggered by {get_user(update)}")
        response_text = (
            "Ура спасибо! Клуб живет за счет волонтеров, которые делают презентации, так что нам это очень кстати!\n\n"
            "Принцип заключается в том, что на обсуждение на звонках приходят только те люди, кто уже сам прочитал главу, "
            "так что твоя презентация не должна покрывать и пересказывать всю главу. Ты можешь сосредоточиться только на "
            "том, что особенно тебя заинтересовало!\n\n"
            "➡️ Что если я прочитала главу, но не поняла ее полностью? Отлично, для того мы и ходим на звонки, чтобы "
            "осудить, кто что понял, а кто что не понял. Абсолютно нормально, если в какой-то части презентации ты скажешь "
            "'автор пишет вот это, я поняла это вот так, но не уверена, что это правильно. Как вы поняли это?'\n\n"
            "Ценность звонков — именно в обсуждении и обмене опытом.\n\n"
            "Когде решишься, просто найди свободный слот в расписании и запишись в "
            "<a href='https://docs.google.com/spreadsheets/d/1qsuaSn0ZkBmldY8hVnKWe41sSgaPG8ekd83csSUh5Qk/edit?gid=0#gid=0'>таблицу</a>. "
            "После звонка пожалуйста оставь ссылку на свои слайды, чтобы другие могли при желании к ним вернуться. "
            "Никого спрашивать и ничего согласовывать не надо.")
        button_list = [
            InlineKeyboardButton("Назад", callback_data="back"),
        ]
        menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response_text,
            reply_markup=InlineKeyboardMarkup(menu),
            parse_mode="HTML")
        return


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
