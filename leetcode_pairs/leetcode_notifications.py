import datetime
import logging

from telegram.ext import ContextTypes

import models
from leetcode_pairs import generate_graph
import helpers
import settings
from zoneinfo import ZoneInfo


async def send_leetcode_pairs_to_group(context: ContextTypes.DEFAULT_TYPE,
                                       generate_graph_obj: generate_graph.GenerateLeetcodeMocks):
    emoji = helpers.random_neutral_emoji()
    notification_str: str = ""
    if len(generate_graph_obj.pairs) > 0:
        notification_str += f"Пары на эту неделю:\n\n"
        for pair in generate_graph_obj.pairs:
            notification_str += f"{emoji} @{pair.first.tg_username} — @{pair.second.tg_username}\n"
        notification_str += f"Напиши партнеру и договорись о времени!\n\n"
    else:
        notification_str += "Пар на этой неделе нет 😢\n\n"

    # todo: handle NULL usernames
    if len(generate_graph_obj.without_pairs) > 0:
        notification_str += "Без пары на этой неделе "
        notification_str += ", ".join([f"@{user.tg_username}" for user in generate_graph_obj.without_pairs])
        notification_str += ". Можно написать в личку и договориться о моке!\n"

    await context.bot.send_message(
        chat_id=settings.CLUB_GROUP_CHAT_ID,
        message_thread_id=settings.LEETCODE_MOCKS_THREAD_ID,
        text=notification_str
    )


async def unicast_leetcode_partner(context: ContextTypes.DEFAULT_TYPE,
                                   generate_graph_obj: generate_graph.GenerateLeetcodeMocks):
    logging.info(f"in unicast_leetcode_partner: {generate_graph_obj.pairs=}")
    # todo: handle NULL usernames
    # todo: add info about chosen timeslots
    for pair in generate_graph_obj.pairs:
        await context.bot.send_message(
            chat_id=pair.first.tg_id,
            text=f"Твоя пара на Leetcode мок: @{pair.second.tg_username}. Напиши партнеру и договорись о времени!",
            parse_mode="HTML")
        await context.bot.send_message(
            chat_id=pair.second.tg_id,
            text=f"Твоя пара на Leetcode мок: @{pair.first.tg_username}. Напиши партнеру и договорись о времени!",
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
