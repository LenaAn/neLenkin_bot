import random

import logging
from sqlalchemy.orm import Session
from telegram import User, Update, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional

import models


def get_user(update: Update) -> Optional[User]:
    if hasattr(update, "callback_query") and update.callback_query:
        return update.callback_query.from_user
    if hasattr(update, "message") and update.message:
        return update.message.from_user


def repr_user(user: Optional[User]) -> str:
    if not user:
        return "Unknown user"
    else:
        return f"User(username={user.username}, id={user.id})"


def repr_user_from_update(update: Update) -> str:
    return repr_user(get_user(update))


def main_menu() -> InlineKeyboardMarkup:
    with Session(models.engine) as session:
        active_courses = session.query(models.Course).filter(models.Course.is_active.is_(True)).all()
        logging.info(f"{active_courses=}")

    button_list = [
        [InlineKeyboardButton("Как вступить?", callback_data="how_to_join")],
    ]

    for course in active_courses:
        button_list.append([InlineKeyboardButton(course.one_liner if course.one_liner else f"{course.name}",
                                                 callback_data=f"course_info:{course.id}")])

    button_list.append([InlineKeyboardButton("🌟Подписка", callback_data="membership")])

    return InlineKeyboardMarkup(button_list)


def back_menu() -> InlineKeyboardMarkup:
    button_list = [
        InlineKeyboardButton("Назад", callback_data="back"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    return InlineKeyboardMarkup(menu)


def join_menu() -> InlineKeyboardMarkup:
    button_list = [
        InlineKeyboardButton("Вступить", url="https://t.me/lenka_ne_club"),
        InlineKeyboardButton("Назад", callback_data="back"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    return InlineKeyboardMarkup(menu)


def random_neutral_emoji() -> str:
    return random.choice(["🦆", "🦄", "🐞", "🐢", "🐳", "🦒", "🍄", "🌸", "🥕", "🐇", "🕊", "🌿", "🐲", "🐊", "🍡", "🍧", "🍤", "🍓"])
