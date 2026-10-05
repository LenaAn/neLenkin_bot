import datetime
import logging
from zoneinfo import ZoneInfo

from telegram.ext import ContextTypes

import models
from random_coffee import generate_random_coffee_graph
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


async def send_random_coffee_pairs_to_group(context: ContextTypes.DEFAULT_TYPE,
                                            generate_graph_obj: generate_random_coffee_graph.GenerateRandomCoffeePairs):
    emoji = helpers.random_neutral_emoji()
    notification_str: str = ""
    if len(generate_graph_obj.pairs) > 0:
        notification_str += (f"Пары для (не) Ленкин клуб составлены!\n"
                             f"Ищи в списке ниже, с кем встречаешься на этой неделе:\n")
        for pair in generate_graph_obj.pairs:
            notification_str += f"{emoji} {helpers.print_user(pair.first)} — {helpers.print_user(pair.second)}\n"
        notification_str += f"\nНапиши собеседнику в личку, чтобы договориться об удобном времени и формате встречи☕️!\n"
    else:
        notification_str += "На этой неделе не удалось создать пар на Random Coffee 😢\n\n"

    if len(generate_graph_obj.without_pairs) > 0:
        notification_str += "Не хватило пары:\n"
        notification_str += "\n➪ ".join([f"{helpers.print_user(user)}" for user in generate_graph_obj.without_pairs])
        notification_str += "\nНапиши ему\ей, если не успел(а) отметиться, и хочешь встречу на этой неделе.\n"

    await context.bot.send_message(
        chat_id=settings.CLUB_GROUP_CHAT_ID,
        message_thread_id=settings.RANDOM_COFFEE_THREAD_ID,
        text=notification_str,
        parse_mode="HTML"
    )


def format_info_about_partner(user: models.User, signup: models.MockSignUp) -> str:
    msg: str = f"Твоя пара на Random Coffee: {helpers.print_user(user)}."
    msg += "\n\nНапиши партнеру и договорись о времени!"
    return msg


async def unicast_random_coffee_partner(context: ContextTypes.DEFAULT_TYPE,
                                        generate_graph_obj: generate_random_coffee_graph.GenerateRandomCoffeePairs) -> None:
    logging.info(f"in unicast_random_coffee_partner: {generate_graph_obj.pairs=}")

    tg_id_to_signup = {}
    for signup in generate_graph_obj.sign_ups:
        tg_id_to_signup[signup.tg_id] = signup

    for pair in generate_graph_obj.pairs:
        await context.bot.send_message(
            chat_id=pair.first.tg_id,
            text=format_info_about_partner(pair.second, tg_id_to_signup[pair.second.tg_id]),
            parse_mode="HTML")
        await context.bot.send_message(
            chat_id=pair.second.tg_id,
            text=format_info_about_partner(pair.first, tg_id_to_signup[pair.first.tg_id]),
            parse_mode="HTML")

    if len(generate_graph_obj.without_pairs) > 0:
        for alone_user in generate_graph_obj.without_pairs:
            await context.bot.send_message(
                chat_id=alone_user.tg_id,
                text="Тебе на этой неделе не досталось пары на Random Coffee 😢\n\nПопробуй заново на следующей неделе!",
                parse_mode="HTML")


async def handle_random_coffee_pairs_announce(context: ContextTypes.DEFAULT_TYPE):
    generate_graph_obj = generate_random_coffee_graph.GenerateRandomCoffeePairs.build()

    await send_random_coffee_pairs_to_group(context, generate_graph_obj)
    await unicast_random_coffee_partner(context, generate_graph_obj)


async def register_random_coffee_pairs_announce(app):
    app.job_queue.run_daily(
        callback=handle_random_coffee_pairs_announce,
        time=datetime.time(hour=13, minute=6, tzinfo=berlin_tz),
        days=(1,),  # 0 = Sunday, ..., 1 = Monday
        name=f"random_coffee_pairs_announce",
    )
