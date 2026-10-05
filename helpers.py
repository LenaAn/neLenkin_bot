import random
from typing import Optional
import logging

from telegram import Bot, Update, User
from sqlalchemy.orm import Session

import models
import settings


def print_user(user: models.User):
    if user.tg_username:
        return f"@{user.tg_username}"

    safe_name: str = user.first_name if user.first_name else user.tg_id
    return f'<a href="tg://user?id={user.tg_id}">{safe_name}</a>'


async def is_user_in_group(bot: Bot, tg_id: int) -> bool:
    member = await bot.get_chat_member(
        chat_id=settings.CLUB_GROUP_CHAT_ID ,
        user_id=tg_id,
    )

    if member.status in ("member", "administrator", "creator"):
        logging.info(f"User {tg_id} is in group")
        return True
    else:
        logging.info(f"User {tg_id} is NOT in group")
        return False


# returns None if there's no User with this tg_id
# return string 'None' if there's a user without username
def get_username(tg_id: str) -> str | None:
    with (Session(models.engine) as session):
        result = session.query(models.User).filter(models.User.tg_id == tg_id).one_or_none()
        if result:
            return str(result.tg_username)
        else:
            return None


def get_user(update: Update) -> Optional[User]:
    if hasattr(update, "callback_query") and update.callback_query:
        return update.callback_query.from_user
    if hasattr(update, "effective_message") and update.effective_message:
        return update.effective_message.from_user


def repr_user(user: Optional[User]) -> str:
    if not user:
        return "Unknown user"
    else:
        return f"User(username={user.username}, id={user.id})"


def repr_user_from_update(update: Update) -> str:
    return repr_user(get_user(update))


def random_neutral_emoji() -> str:
    return random.choice(["🦆", "🦄", "🐞", "🐢", "🐳", "🦒", "🍄", "🌸", "🥕", "🐇", "🕊", "🌿", "🐲", "🐊", "🍡", "🍧", "🍤", "🍓"])
