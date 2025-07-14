import logging

from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, User
from telegram.ext import (CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler,
                          filters)

import constants
import helpers
import models
import settings


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
        "sre_enroll": handle_sre_enroll,
        "sre_unenroll": handle_sre_unenroll,
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


def user_is_enrolled(tg_user: User, course_id: int) -> bool:
    with Session(models.engine) as session:
        users_exists = session.scalar(
            select(exists().where(
                (models.Enrollment.tg_id == str(tg_user.id)) & (models.Enrollment.course_id == course_id))
            )
        )
    if users_exists:
        logging.info(f"user is already enrolled in {constants.id_to_course[course_id]}: {tg_user}")
    else:
        logging.info(f"user is not already enrolled in {constants.id_to_course[course_id]}: {tg_user}")
    return users_exists


async def handle_course_info(update: Update, course_id: int, course_description: str, enroll_description: str,
                             cta_description: str, enroll_callback: str, unenroll_callback: str) -> None:
    tg_user = helpers.get_user(update)
    logging.info(f"handle_course_info for {constants.id_to_course[course_id]} triggered by {tg_user}")

    if user_is_enrolled(tg_user, course_id):
        button_list = [
            InlineKeyboardButton("Перестать получать уведомления", callback_data=unenroll_callback),
            InlineKeyboardButton("Назад", callback_data="back"),
        ]
        menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
        await update.callback_query.edit_message_text(
            text=course_description + "\n\n" + enroll_description,
            reply_markup=InlineKeyboardMarkup(menu),
            parse_mode="HTML")
    else:
        button_list = [
            InlineKeyboardButton("Хочу участвовать!", callback_data=enroll_callback),
            InlineKeyboardButton("Назад", callback_data="back"),
        ]
        menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
        await update.callback_query.edit_message_text(
            text=course_description + "\n\n" + cta_description,
            reply_markup=InlineKeyboardMarkup(menu),
            parse_mode="HTML")


async def handle_mock_leetcode(update: Update) -> None:
    await handle_course_info(update, constants.leetcode_course_id, constants.mock_leetcode_description,
                             constants.leetcode_enroll_description, constants.leetcode_cta_description,
                             "leetcode_enroll", "leetcode_unenroll")


async def handle_sre_book(update: Update) -> None:
    await handle_course_info(update, constants.sre_course_id, constants.sre_book_description,
                             constants.sre_enroll_description, constants.sre_book_cta_description,
                             "sre_enroll", "sre_unenroll")


async def handle_enroll(update: Update, course_id: int, unenroll_callback_data: str, enroll_description: str) -> None:
    tg_user = helpers.get_user(update)
    logging.info(f"enroll for {constants.id_to_course[course_id]} handled by {tg_user}")

    with Session(models.engine) as session:
        enrollment = models.Enrollment(
            course_id=course_id,
            tg_id=tg_user.id
        )
        session.add(enrollment)
        try:
            session.commit()
            logging.info(f"Add user enrollment to {constants.id_to_course[course_id]} to db: {tg_user}")
        except IntegrityError as e:
            session.rollback()
            logging.info(f"Didn't add user {tg_user.username} enrollment to {constants.id_to_course[course_id]} to db: {e}")
        except Exception as e:
            session.rollback()
            logging.warning(f"Couldn't add user enrollment to {constants.id_to_course[course_id]}: {e}")
    button_list = [
        InlineKeyboardButton("Перестать получать уведомления", callback_data=unenroll_callback_data),
        InlineKeyboardButton("Назад", callback_data="back"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    await update.callback_query.edit_message_text(
        text=enroll_description,
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML"
    )


async def handle_unenroll(update: Update, course_id: int, unenroll_description: str) -> None:
    tg_user = helpers.get_user(update)
    logging.info(f"unenroll for {constants.id_to_course[course_id]} handled by {tg_user}")

    with Session(models.engine) as session:
        try:
            session.query(models.Enrollment).filter(
                (models.Enrollment.tg_id == str(tg_user.id)) & (models.Enrollment.course_id == course_id)).delete()
            session.commit()
            logging.info(f"Deleted user enrollment to {constants.id_to_course[course_id]} from db: {tg_user}")
        except Exception as e:
            session.rollback()
            logging.error(f"Couldn't delete user enrollment to {constants.id_to_course[course_id]}: {e}")
            raise e  # to propagate it to error handler

    button_list = [
        InlineKeyboardButton("Назад", callback_data="back"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    await update.callback_query.edit_message_text(
        text=unenroll_description,
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML"
    )


async def handle_leetcode_enroll(update: Update) -> None:
    await handle_enroll(
        update,
        constants.leetcode_course_id,
        "leetcode_unenroll",
        constants.leetcode_enroll_description)


async def handle_leetcode_unenroll(update: Update) -> None:
    await handle_unenroll(update, constants.leetcode_course_id, constants.leetcode_unenroll_description)


async def handle_sre_enroll(update: Update) -> None:
    await handle_enroll(
        update,
        constants.sre_course_id,
        "sre_unenroll",
        constants.sre_enroll_description)


async def handle_sre_unenroll(update: Update) -> None:
    await handle_unenroll(update, constants.sre_course_id, constants.sre_unenroll_description)


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


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    # todo: ignore "Message is not modified" and "Query is too old" errors?
    if not isinstance(update, Update):
        logging.info(f"error by not even update: {update}, exc_info=context.error")
    else:
        logging.info(f"error triggered by {helpers.get_user(update)}", exc_info=context.error)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=constants.error_description,
            parse_mode="HTML")

        await context.bot.send_message(
            chat_id=settings.ADMIN_CHAT_ID,
            text=f"error triggered by {helpers.get_user(update)}: {context.error}",
            parse_mode="HTML")


LEETCODE_FIRST_PROBLEM, LEETCODE_SECOND_PROBLEM, LEETCODE_TIMESLOTS, LEETCODE_PROGRAMMING_LANGUAGE, LEETCODE_ENGLISH =\
    range(5)


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
        # todo: leetcode_register should work only after announcing topic on monday till Thursday evening, other time
        # it should say "wait"
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
