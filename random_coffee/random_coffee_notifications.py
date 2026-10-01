import datetime
import logging
from zoneinfo import ZoneInfo

from telegram.ext import ContextTypes
from telegram import Update

import helpers
import settings

random_coffee_logger = logging.getLogger(__name__)
random_coffee_logger.setLevel(logging.INFO)


async def handle_random_coffee_poll(context: ContextTypes.DEFAULT_TYPE):
    message = await context.bot.send_poll(
        chat_id=settings.CLUB_GROUP_CHAT_ID,
        message_thread_id=settings.RANDOM_COFFEE_THREAD_ID,
        question="Привет, будешь участвовать во встречах Random Coffee на следующей неделе? ☕️",
        options=[f"Да!{helpers.random_neutral_emoji()}", "Не в этот раз🤷🏻‍♀️"],
        is_anonymous=False,
        allows_multiple_answers=False,
        open_period=2*24*60*60   # 2 days, posted on Friday afternoon, closed on Sunday afternoon
    )
    random_coffee_logger.info(f"Sent a poll about Random Coffee, {message.poll.id=}")


async def handle_poll_answer(update: Update, _: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    poll_id = answer.poll_id
    user_id = answer.user.id
    option_ids = answer.option_ids

    random_coffee_logger.info(f"Got a poll vote: {user_id=}, {poll_id=}, {option_ids=}")


# no matter winter or summer time in Europe.
# In theory should work without restart when the time changes
berlin_tz = ZoneInfo("Europe/Berlin")


async def register_random_coffee_poll(app):
    app.job_queue.run_daily(
        callback=handle_random_coffee_poll,
        time=datetime.time(hour=16, minute=6, tzinfo=berlin_tz),
        days=(5,),  # 0 = Sunday, ..., 5 = Friday
        name=f"random_coffee_poll",
    )
