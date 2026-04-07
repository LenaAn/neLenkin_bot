import os
import logging

from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from telegram import Update
from telegram.ext import ContextTypes

import helpers
import models


async def set_email_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"set_email_handler triggered by {helpers.repr_user_from_update(update)}")

    args = context.args
    if len(args) != 1:
        await update.message.reply_text("Введи email сразу в команде, вот так: /set_email email@example.com")
        return

    email = args[0]
    tg_id = str(update.effective_user.id)
    with Session(models.engine) as session:
        stmt = postgresql.insert(models.UserEmail).values(
            tg_id=tg_id,
            contact_email=email,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["tg_id"],
            set_={
                "contact_email": email,
            }
        )

        session.execute(stmt)
        session.commit()
    logging.info(f"New contact email for {helpers.repr_user_from_update(update)}: {email}")
    await update.message.reply_text(f"Твой email сохранен: {email}.\n\nТеперь ссылка на звонки клуба будет приходить и "
                                    f"на этот email за 5 минут до встречи.\n\nЧтобы поменять email, вызови команду "
                                    f"заново.\n\nЧтобы удалить email, напиши @lenka_colenka")

    admin_chat_id = int(os.getenv('ADMIN_CHAT_ID'))
    await context.bot.send_message(
        chat_id=admin_chat_id,
        text=f"New contact email for {helpers.repr_user_from_update(update)}: {email}",
    )
