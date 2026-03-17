import random

from telegram import User, Update
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


def random_neutral_emoji() -> str:
    return random.choice(["🦆", "🦄", "🐞", "🐢", "🐳", "🦒", "🍄", "🌸", "🥕", "🐇", "🕊", "🌿", "🐲", "🐊", "🍡", "🍧", "🍤", "🍓"])
