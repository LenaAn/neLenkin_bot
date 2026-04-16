import datetime
import logging

from telegram.ext import ContextTypes

import constants
import models
from leetcode_pairs import generate_graph
import helpers
import settings
from zoneinfo import ZoneInfo


def print_user(user: models.User):
    if user.tg_username:
        return f"@{user.tg_username}"

    safe_name: str = user.first_name if user.first_name else user.tg_id
    return f'<a href="tg://user?id={user.tg_id}">{safe_name}</a>'


async def send_leetcode_pairs_to_group(context: ContextTypes.DEFAULT_TYPE,
                                       generate_graph_obj: generate_graph.GenerateLeetcodeMocks):
    emoji = helpers.random_neutral_emoji()
    notification_str: str = ""
    if len(generate_graph_obj.pairs) > 0:
        notification_str += f"Пары на эту неделю:\n\n"
        for pair in generate_graph_obj.pairs:
            notification_str += f"{emoji} {print_user(pair.first)} — {print_user(pair.second)}\n"
        notification_str += f"Напиши партнеру и договорись о времени!\n\n"
    else:
        notification_str += "Пар на этой неделе нет 😢\n\n"

    if len(generate_graph_obj.without_pairs) > 0:
        notification_str += "Без пары на этой неделе "
        notification_str += ", ".join([f"{print_user(user)}" for user in generate_graph_obj.without_pairs])
        notification_str += ". Можно написать в личку и договориться о моке!\n"

    await context.bot.send_message(
        chat_id=settings.CLUB_GROUP_CHAT_ID,
        message_thread_id=settings.LEETCODE_MOCKS_THREAD_ID,
        text=notification_str,
        parse_mode="HTML"
    )


def format_info_about_partner(user: models.User, signup: models.MockSignUp, my_english: bool) -> str:
    msg: str = f"Твоя пара на Leetcode мок: {print_user(user)}."

    timeslots_string = "\n - ".join([constants.leetcode_register_timeslots[i] for i in signup.selected_timeslots])
    msg += f"\n\nПартнеру удобны слоты (по Московскому времени):\n - {timeslots_string}"

    if my_english and signup.english_choice:
        msg += f"\n\nМок будет на английском языке."
    else:
        msg += f"\n\nМок будет на русском языке."

    msg += f"\n\nПартнер будет решать задачу на языке {signup.programming_language}."
    msg += "\n\nНапиши партнеру и договорись о времени!"
    return msg


async def unicast_leetcode_partner(context: ContextTypes.DEFAULT_TYPE,
                                   generate_graph_obj: generate_graph.GenerateLeetcodeMocks) -> None:
    logging.info(f"in unicast_leetcode_partner: {generate_graph_obj.pairs=}")

    tg_id_to_signup = {}
    for signup in generate_graph_obj.sign_ups:
        tg_id_to_signup[signup.tg_id] = signup

    for pair in generate_graph_obj.pairs:
        await context.bot.send_message(
            chat_id=pair.first.tg_id,
            text=format_info_about_partner(pair.second, tg_id_to_signup[pair.second.tg_id],
                                           tg_id_to_signup[pair.first.tg_id].english_choice),
            parse_mode="HTML")
        await context.bot.send_message(
            chat_id=pair.second.tg_id,
            text=format_info_about_partner(pair.first, tg_id_to_signup[pair.first.tg_id],
                                           tg_id_to_signup[pair.second.tg_id].english_choice),
            parse_mode="HTML")

    if len(generate_graph_obj.without_pairs) > 0:
        for alone_user in generate_graph_obj.without_pairs:
            await context.bot.send_message(
                chat_id=alone_user.tg_id,
                text="Тебе на этой неделе не досталось пары на Leetcode мок 😢\n\nПопробуй заново на следующей неделе!",
                parse_mode="HTML")


async def leetcode_notifications(context: ContextTypes.DEFAULT_TYPE):
    if not models.leetcode_status_on:
        logging.info("Skipping creating Leetcode mock pairs because leetcode if off")
        await context.bot.send_message(
            chat_id=settings.ADMIN_CHAT_ID,
            text="Skipping creating Leetcode mock pairs because leetcode if off",
            parse_mode="HTML")
        return

    generate_graph_obj = generate_graph.GenerateLeetcodeMocks.build(
        week_number=datetime.date.today().isocalendar().week)

    await send_leetcode_pairs_to_group(context, generate_graph_obj)
    await unicast_leetcode_partner(context, generate_graph_obj)


async def register_leetcode_pairs_notification(app):
    # no matter winter or summer time in Europe.
    # In theory should work without restart when the time changes
    berlin_tz = ZoneInfo("Europe/Berlin")

    app.job_queue.run_daily(
        callback=leetcode_notifications,
        time=datetime.time(hour=9, minute=3, tzinfo=berlin_tz),
        days=(5,),  # 0 = Sunday, ..., 5 = Friday
        name=f"leetcode_pairs_notification",
    )
