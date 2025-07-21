import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler,
                          filters)

import constants
import helpers
import models

LEETCODE_FIRST_PROBLEM, LEETCODE_SECOND_PROBLEM, LEETCODE_TIMESLOTS, LEETCODE_PROGRAMMING_LANGUAGE, LEETCODE_ENGLISH = \
    range(5)


def is_leetcode_on(callback):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not models.leetcode_status_on:
            logging.info(f"is_leetcode_on check triggered by {helpers.get_user(update)}, leetcode is OFF")
            await update.effective_chat.send_message(
                "❌ Запись на эти выходные уже закрыта. Подожди понедельника, когда объявят тему новой недели")
            return None
        logging.info(f"is_leetcode_on check triggered by {helpers.get_user(update)}, leetcode is ON")
        return await callback(update, context, *args, **kwargs)

    return wrapper


@is_leetcode_on
async def start_leetcode_register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
    logging.info(f"start_leetcode_register handler triggered by {helpers.get_user(update)}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Пришли ссылку на задачу, которую ты будешь спрашивать как интервьюер.\n\n"
             f"Пример: https://leetcode.com/problems/two-sum/description/"
    )
    return LEETCODE_FIRST_PROBLEM


@is_leetcode_on
async def leetcode_first_problem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"leetcode_first_problem handler triggered by {helpers.get_user(update)}, first problem is "
                 f"{update.message.text}")
    context.user_data["first_problem"] = update.message.text
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Отлично! Теперь пришли ссылку на запасную задачу, на случай, если партнер уже решал основную задачу.\n\n"
             f"Пример: https://leetcode.com/problems/two-sum/description/"
    )
    return LEETCODE_SECOND_PROBLEM


def create_timeslots(_: Update, context: ContextTypes.DEFAULT_TYPE):
    button_list = []
    for i, option in enumerate(constants.leetcode_register_timeslots):
        checked = "✅ " if i in context.user_data["selected_timeslots"] else ""
        button_list.append([
            InlineKeyboardButton(f"{checked}{option}", callback_data=f"leetcode_timeslot_{i}")
        ])

    if len(context.user_data["selected_timeslots"]) >= 3:
        button_list.append([InlineKeyboardButton("➡️ Продолжить", callback_data="leetcode_timeslot_continue")])

    return button_list


@is_leetcode_on
async def leetcode_second_problem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"leetcode_second_problem handler triggered by {helpers.get_user(update)}, "
                 f"user data = {context.user_data}, second problem is {update.message.text}")
    context.user_data["second_problem"] = update.message.text

    if "selected_timeslots" not in context.user_data:
        context.user_data["selected_timeslots"] = set()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=constants.leetcode_register_ask_timeslots,
        reply_markup=InlineKeyboardMarkup(create_timeslots(update, context)),
        parse_mode="HTML")
    return LEETCODE_TIMESLOTS


async def edit_timeslots(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"edit_timeslots handler triggered by {helpers.get_user(update)}, user data = {context.user_data}, "
                 f"update = {update.callback_query.data}")

    await update.callback_query.edit_message_text(
        text=constants.leetcode_register_ask_timeslots,
        reply_markup=InlineKeyboardMarkup(create_timeslots(update, context)),
        parse_mode="HTML")
    return LEETCODE_TIMESLOTS


@is_leetcode_on
async def leetcode_timeslot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"leetcode_timeslot_handler handler triggered by {helpers.get_user(update)}, "
                 f"user data = {context.user_data}, update = {update.callback_query.data}")
    # save info about timeslots
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    if not query.data.startswith("leetcode_timeslot_"):
        raise ValueError(f"Unexpected callback, data={query.data}, user={helpers.get_user(update)}")

    arg = query.data.split("_")[-1]
    if arg.isnumeric():
        idx = int(arg)
        if idx in context.user_data["selected_timeslots"]:
            context.user_data["selected_timeslots"].remove(idx)
        else:
            context.user_data["selected_timeslots"].add(idx)
        await edit_timeslots(update, context)
    else:
        logging.info(f"user continued in timeslots, selected_timeslots timeslots = "
                     f"{context.user_data['selected_timeslots']}, arg={arg}")
        if arg != "continue":
            raise ValueError(f"Unexpected callback, data={query.data}, user={helpers.get_user(update)}")
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"На каком языке программирования будешь решать задачу?\n\n"
                     f"Пример: Python"
            )
            return LEETCODE_PROGRAMMING_LANGUAGE


@is_leetcode_on
async def leetcode_programming_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"leetcode_programming_language handler triggered by {helpers.get_user(update)}, "
                 f"user data = {context.user_data}, programming language = {update.message.text}")
    context.user_data["leetcode_programming_language"] = update.message.text

    button_list = [
        [InlineKeyboardButton(f"Да", callback_data=f"leetcode_english_yes")],
        [InlineKeyboardButton(f"Нет", callback_data=f"leetcode_english_no")]
    ]

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Готов проходить мок-собеседование на английском?",
        reply_markup=InlineKeyboardMarkup(button_list),
        parse_mode="HTML"
    )
    return LEETCODE_ENGLISH


@is_leetcode_on
async def leetcode_english(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()  # Acknowledge the callback
    logging.info(f"leetcode_english handler triggered by {helpers.get_user(update)}, user data = {context.user_data}, "
                 f"english_choice = {update.callback_query.data}")
    if update.callback_query.data == "leetcode_english_yes":
        context.user_data["leetcode_english"] = True
    elif update.callback_query.data == "leetcode_english_no":
        context.user_data["leetcode_english"] = False
    else:
        raise ValueError(f"Unexpected callback_data = {update.callback_query.data} by {helpers.get_user(update)}")

    english_string = 'Мок будет на английском, если партнер тоже может на англиском, иначе на русском' \
        if context.user_data['leetcode_english'] else 'Мок будет на русском языке'
    timeslots_string = ", ".join(
        [constants.leetcode_register_timeslots[i] for i in context.user_data['selected_timeslots']])

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"<b>Твой выбор</b>\n\n"
             f"Основная задача: {context.user_data['first_problem']}\n"
             f"Запасная задача: {context.user_data['second_problem']}\n"
             f"Выбранные таймслоты: {timeslots_string + ' по Московскому времени'}\n"
             f"Язык программирования: {context.user_data['leetcode_programming_language']}\n"
             f"{english_string}\n\n"
             f"В пятницу утром я объявлю твоего партнера на эту неделю\n\n"
             f"Если хочешь изменить свой выбор, используй команду /leetcode_register. Если не хочешь участвовать в "
             f"мок-собеседовании на этой неделе, используй команду /cancel_leetcode_register. Если есть вопросы, напиши"
             f" @lenka_colenka",
        parse_mode="HTML"
    )
    # todo: save to db
    return ConversationHandler.END


async def cancel_leetcode_register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info(f"cancel_leetcode_register handler triggered by {helpers.get_user(update)}")
    if "first_problem" in context.user_data:
        del context.user_data["first_problem"]
    if "second_problem" in context.user_data:
        del context.user_data["second_problem"]
    if "selected_timeslots" in context.user_data:
        del context.user_data["selected_timeslots"]
    if "leetcode_programming_language" in context.user_data:
        del context.user_data["leetcode_programming_language"]
    if "leetcode_english" in context.user_data:
        del context.user_data["leetcode_english"]

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Ты не будешь участвовать в мок-собеседовании на этой неделе")
    return ConversationHandler.END


leetcode_register_handler = ConversationHandler(
    entry_points=[
        CommandHandler('leetcode_register', start_leetcode_register),
        CallbackQueryHandler(start_leetcode_register, '^leetcode_register$')
    ],
    states={
        LEETCODE_FIRST_PROBLEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, leetcode_first_problem)],
        LEETCODE_SECOND_PROBLEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, leetcode_second_problem)],
        LEETCODE_TIMESLOTS: [CallbackQueryHandler(leetcode_timeslot_handler, "^leetcode_timeslot")],
        LEETCODE_PROGRAMMING_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, leetcode_programming_language)],
        LEETCODE_ENGLISH: [CallbackQueryHandler(leetcode_english, "^leetcode_english")]
    },
    fallbacks=[CommandHandler('leetcode_register', start_leetcode_register),
               CallbackQueryHandler(start_leetcode_register, '^leetcode_register$'),
               CommandHandler('cancel_leetcode_register', cancel_leetcode_register)],
)
