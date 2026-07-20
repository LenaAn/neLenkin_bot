import logging

from sqlalchemy.orm import Session
from telegram import Update
from telegram.ext import ContextTypes

import helpers
import models

membership_logger = logging.getLogger(__name__)
membership_logger.setLevel(logging.INFO)


async def handle_club_points(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = helpers.get_user(update)
    membership_logger.info(f"handle_club_points triggered by {tg_user}")

    club_points = 0
    with (Session(models.engine) as session):
        result = session \
            .query(models.ClubPoints.balance)\
            .filter(models.ClubPoints.tg_id == str(tg_user.id)).one_or_none()
        if result:
            club_points = result[0]
            logging.info(f"{tg_user.id} has {club_points} 🌟ClubPoints")

    msg: str = (f"У тебя {club_points} 🌟ClubPoints"
                f"\n\n • Если у тебя закончится 💜Pro подписка, 1000 ClubPoints автоматически конвертируются в месяц "
                f"Pro подписки."
                f"\n\n • ClubPoints зачисляются за презентации, если у тебя уже есть Pro."
                f"\n\n • Узнать статус подписки можно командой /membership")

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=msg,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
