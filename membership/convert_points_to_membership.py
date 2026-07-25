import datetime
import logging
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session
from telegram.ext import ContextTypes

import helpers
from membership import membership, update_membership, fetch_boosty_patrons, fetch_patrons
import models
import settings

membership_logger = logging.getLogger(__name__)
membership_logger.setLevel(logging.INFO)


async def do_convert_points_to_membership(context: ContextTypes.DEFAULT_TYPE):
    await fetch_boosty_patrons.load_boosty_patrons(context.bot)
    await fetch_patrons.load_patrons(context.bot)

    with (Session(models.engine) as session):
        users_with_enough_points = session.query(models.ClubPoints.tg_id).filter(models.ClubPoints.balance >= 1000
                                                                                 ).all()

    for result in users_with_enough_points:
        tg_id = result[0]
        membership_info = membership.get_user_membership_info(tg_id)
        if membership_info.get_overall_level() == membership.basic:
            point_count, new_balance = update_membership.do_substract_points(tg_id, 1000)
            if new_balance is not None:
                days_count, new_expiry = update_membership.do_add_days(tg_id, 31)
                await context.bot.send_message(
                    chat_id=settings.ADMIN_CHAT_ID,
                    text=f"Exchanged 1000 points to 1 month of membership by activity for {helpers.get_username(tg_id)}, "
                         f"new balance is {new_balance}, membership expiry is {new_expiry}"
                )
                await context.bot.send_message(
                    chat_id=tg_id,
                    text=f"1000 🌟ClubPoints были автоматически конвертированы в месяц 💜Pro подписки!"
                         f"\n\nТекущий баланс: {new_balance} поинтов"
                         f"\n\nТвоя Pro подписка за активность истекает {new_expiry}."
                )
            else:
                await context.bot.send_message(
                    chat_id=settings.ADMIN_CHAT_ID,
                    text=f"Could not exchange points to membership for {helpers.get_username(tg_id)}"
                )


async def register_convert_points_to_membership(app):
    berlin_tz = ZoneInfo("Europe/Berlin")

    app.job_queue.run_daily(
        callback=do_convert_points_to_membership,
        # 25 min before sending out patreon prompts
        time=datetime.time(hour=9, minute=30, tzinfo=berlin_tz),
        name=f"convert_points_to_membership",
    )
