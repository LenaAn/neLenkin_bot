import logging

from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, User
from telegram.ext import ContextTypes

import constants
import helpers
import models


def user_is_enrolled(tg_user: User, course_id: int) -> bool:
    with Session(models.engine) as session:
        users_exists = session.scalar(
            select(exists().where(
                (models.Enrollment.tg_id == str(tg_user.id)) & (models.Enrollment.course_id == course_id))
            )
        )
    if users_exists:
        logging.info(f"user is already enrolled in {constants.id_to_course[course_id]}: {helpers.repr_user(tg_user)}")
    else:
        logging.info(
            f"user is not already enrolled in {constants.id_to_course[course_id]}: {helpers.repr_user(tg_user)}")
    return users_exists


async def handle_course_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    course_id = context.user_data["callback_course_id"]
    del context.user_data["callback_course_id"]
    logging.info(f"handle_course_info for {constants.id_to_course[course_id]} triggered by "
                 f"{helpers.repr_user_from_update(update)}")

    tg_user = helpers.get_user(update)
    if user_is_enrolled(tg_user, course_id):
        button_list = [
            InlineKeyboardButton("Перестать получать уведомления", callback_data=f"unenroll:{course_id}"),
            InlineKeyboardButton("Назад", callback_data="back_to_courses"),
        ]
        menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
        await update.callback_query.edit_message_text(
            text=constants.id_to_description[course_id] + "\n\n" + constants.id_to_enroll_description[course_id],
            reply_markup=InlineKeyboardMarkup(menu),
            parse_mode="HTML")
    else:
        button_list = [
            InlineKeyboardButton("Хочу участвовать!", callback_data=f"enroll:{course_id}"),
            InlineKeyboardButton("Назад", callback_data="back_to_courses"),
        ]
        menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
        await update.callback_query.edit_message_text(
            text=constants.id_to_description[course_id] + "\n\n" + constants.id_to_cta[course_id],
            reply_markup=InlineKeyboardMarkup(menu),
            parse_mode="HTML")


async def handle_active_courses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"handle_active_courses triggered by {helpers.repr_user_from_update(update)}")

    tg_id = str(update.effective_user.id)

    with Session(models.engine) as session:
        active_courses = session.query(models.Course).filter(models.Course.is_active.is_(True)).all()
        user_enrollments = session.query(models.Enrollment.course_id).filter(models.Enrollment.tg_id == tg_id).all()
        enrolled_course_ids = {e.course_id for e in user_enrollments}

        logging.info(f"{active_courses=}")
        logging.info(f"{enrolled_course_ids=}")

    button_list = []
    for course in active_courses:
        course_name = course.one_liner if course.one_liner else course.name
        course_level = "🔒" if course.is_pro else "🆓"

        is_enrolled = course.id in enrolled_course_ids
        enrollment_marker = "➕" if is_enrolled else "➖"

        button_list.append([InlineKeyboardButton(f"{enrollment_marker} {course_name} {course_level}",
                                                 callback_data=f"course_info:{course.id}")])

    courses_description = ('Потоки которые идут прямо сейчас!\n\n'
                           'Можно подписаться на поток и получать новости об этом потоке! '
                           'Некоторые курсы открыты всем 🆓, для некоторых нужна подписка 🔒.\n\n'
                           'Узнать свой уровень подписки и оформить 💜Pro можно по команде /membership')

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=courses_description,
            reply_markup=InlineKeyboardMarkup(button_list)
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=courses_description,
            reply_markup=InlineKeyboardMarkup(button_list)
        )


async def handle_enroll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    course_id = context.user_data["callback_course_id"]
    del context.user_data["callback_course_id"]
    logging.info(f"enroll for {constants.id_to_course[course_id]} handled by {helpers.repr_user_from_update(update)}")

    tg_user = helpers.get_user(update)
    with Session(models.engine) as session:
        enrollment = models.Enrollment(
            course_id=course_id,
            tg_id=tg_user.id
        )
        session.add(enrollment)
        try:
            session.commit()
            logging.info(f"Add user enrollment to {constants.id_to_course[course_id]} to db: "
                         f"{helpers.repr_user(tg_user)}")
        except IntegrityError as e:
            session.rollback()
            logging.info(f"Didn't add user {helpers.repr_user(tg_user)} enrollment to "
                         f"{constants.id_to_course[course_id]} to db: {e}")
        except Exception as e:
            session.rollback()
            logging.warning(f"Couldn't add user enrollment to {constants.id_to_course[course_id]}: {e}")
    button_list = [
        InlineKeyboardButton("Перестать получать уведомления", callback_data=f"unenroll:{course_id}"),
        InlineKeyboardButton("Назад", callback_data="back_to_courses"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    await update.callback_query.edit_message_text(
        text=constants.id_to_enroll_description[course_id],
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML"
    )


async def handle_unenroll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    course_id = context.user_data["callback_course_id"]
    del context.user_data["callback_course_id"]
    logging.info(f"unenroll for {constants.id_to_course[course_id]} handled by {helpers.repr_user_from_update(update)}")

    tg_user = helpers.get_user(update)
    with Session(models.engine) as session:
        try:
            session.query(models.Enrollment).filter(
                (models.Enrollment.tg_id == str(tg_user.id)) & (models.Enrollment.course_id == course_id)).delete()
            session.commit()
            logging.info(f"Deleted user enrollment to {constants.id_to_course[course_id]} from db: "
                         f"{helpers.repr_user(tg_user)}")
        except Exception as e:
            session.rollback()
            logging.error(f"Couldn't delete user enrollment to {constants.id_to_course[course_id]}: {e}")
            raise e  # to propagate it to error handler

    button_list = [
        InlineKeyboardButton("Назад", callback_data="back_to_courses"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    await update.callback_query.edit_message_text(
        text=constants.id_to_unenroll_description[course_id],
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML"
    )
