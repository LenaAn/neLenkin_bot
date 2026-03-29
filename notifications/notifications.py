import datetime
import logging
import os
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import constants
import models
from models import Enrollment, ScheduledPartMessages, engine
from membership import membership
import settings
from . import notifications_helpers

notifications_logger = logging.getLogger(__name__)
notifications_logger.setLevel(logging.DEBUG)


async def register_notifications(application):
    await register_leetcode_notifications(application)
    await register_sre_notifications(application)
    await register_ddia_notifications(application)
    await register_ddia_prompt_to_connect_patreon_notifications(application)
    # todo: disable courses nicely
    await register_leetcode_grind_notifications(application)
    await register_leetcode_grind_prompt_to_connect_patreon_notifications(application)
    # await register_codecrafters_notifications(application)
    await register_codecrafters_kafka_notifications(application)
    await register_aoc_notifications(application)
    await register_dmls_notifications(application)
    await register_dmls_prompt_to_connect_patreon_notifications(application)


async def handle_leetcode_reminder(context: ContextTypes.DEFAULT_TYPE):
    course_id: int = context.job.data["course_id"]
    if "message" not in context.job.data:
        admin_chat_id = int(os.getenv('ADMIN_CHAT_ID'))
        notifications_logger.error(
            f"Can't handle notification, there's no message in context.job.data: {context.job.data}")
        await context.bot.send_message(
            chat_id=admin_chat_id,
            text=f"Can't handle notification, there's no message in context.job.data: {context.job.data}"
        )
        return

    message: str = context.job.data["message"]
    menu: InlineKeyboardMarkup = context.job.data["menu"] if "menu" in context.job.data else None
    with Session(engine) as session:
        subquery = (
            select(models.MockSignUp.tg_id)
            .where(models.MockSignUp.week_number == datetime.date.today().isocalendar().week)
        )

        result = (
            session.query(Enrollment.tg_id)
            .filter(Enrollment.course_id == course_id)
            .filter(~Enrollment.tg_id.in_(subquery))
            .all()
        )

    notification_chat_ids = [item[0] for item in result]
    notifications_logger.debug(f"handling {constants.id_to_course[course_id]} notification, "
                               f"got {len(notification_chat_ids)} chat ids that are enrolled to Leetcode and not signed "
                               f"for this week")

    await notifications_helpers.do_send_notifications(context, notification_chat_ids, message, menu,
                                                      constants.id_to_course[course_id])


async def handle_notification(context: ContextTypes.DEFAULT_TYPE):
    course_id: int = context.job.data["course_id"]
    if "message" not in context.job.data:
        admin_chat_id = int(os.getenv('ADMIN_CHAT_ID'))
        notifications_logger.error(
            f"Can't handle notification, there's no message in context.job.data: {context.job.data}")
        await context.bot.send_message(
            chat_id=admin_chat_id,
            text=f"Can't handle notification, there's no message in context.job.data: {context.job.data}"
        )
        return

    message: str = context.job.data["message"]
    menu: InlineKeyboardMarkup = context.job.data["menu"] if "menu" in context.job.data else None
    with Session(engine) as session:
        result = session.query(Enrollment.tg_id).filter(Enrollment.course_id == course_id).all()
        notification_chat_ids = [item[0] for item in result]
    notifications_logger.debug(f"handling {constants.id_to_course[course_id]} notification, "
                               f"got {len(notification_chat_ids)} chat ids that are subscribed to the course")

    if membership.is_course_pro(course_id):
        if models.pro_courses_on:
            # only PRO subscribers will get a link for a PRO course
            # Basic subscribers who are subscribed to notifications about this course will get a Patreon link in the morning
            notification_chat_ids = [tg_id for tg_id in notification_chat_ids
                                     if
                                     membership.get_user_membership_info(tg_id).get_overall_level() == membership.pro]
            notifications_logger.debug(f"handling {constants.id_to_course[course_id]} notification, "
                                       f"got {len(notification_chat_ids)} PRO subscribers")
        else:
            notifications_logger.debug(f"Sending a link to everyone because PRO courses are turned off")
            await context.bot.send_message(
                chat_id=settings.ADMIN_CHAT_ID,
                text=f"Sending a link to everyone because PRO courses are turned off",
                parse_mode="HTML")

    await notifications_helpers.do_send_notifications(context, notification_chat_ids, message, menu,
                                                      constants.id_to_course[course_id])


async def handle_sre_notification(context: ContextTypes.DEFAULT_TYPE):
    # todo: we need more nice way of working with feature flags
    # you can't do `from models import sre_notification_on` and use just `sre_notification_on` here
    # because when you import variable from module, it creates a local copy
    if models.sre_notification_on:
        context.job.data["message"] = constants.before_call_reminders[constants.sre_course_id]
        await handle_notification(context)
    else:
        notifications_logger.info("SRE notification is turned off, skipping sending SRE notifications")


async def handle_codecrafters_notification(context: ContextTypes.DEFAULT_TYPE):
    # todo: we need more nice way of working with feature flags
    # you can't do `from models import codecrafters_notification_on` and use just `codecrafters_notification_on` here
    # because when you import variable from module, it creates a local copy
    if models.codecrafters_notification_on:
        context.job.data["message"] = constants.before_call_reminders[constants.codecrafters_course_id]
        await handle_notification(context)
    else:
        notifications_logger.info("CodeCrafters notification is turned off, skipping sending CodeCrafters notifications")


async def handle_codecrafters_kafka_notification(context: ContextTypes.DEFAULT_TYPE):
    # todo: we need more nice way of working with feature flags
    # you can't do `from models import codecrafters_notification_on` and use just `codecrafters_notification_on` here
    # because when you import variable from module, it creates a local copy
    if models.codecrafters_kafka_notification_on:
        context.job.data["message"] = constants.before_call_reminders[constants.codecrafters_kafka_course_id]
        await handle_notification(context)
    else:
        notifications_logger.info("CodeCrafters-Kafka notification is turned off, skipping sending CodeCrafters-Kafka notifications")


async def handle_aoc_notification(context: ContextTypes.DEFAULT_TYPE):
    if models.aoc_notification_on:
        from aoc import fetch_leaderboard
        notifications_logger.debug("Sending an AoC update to the main chat's AoC thread")
        formatted_report = fetch_leaderboard.get_formatted_leaderboard()
        await context.bot.send_message(
            chat_id=settings.CLUB_GROUP_CHAT_ID,
            message_thread_id=settings.AOC_TOPIC_ID,
            text=formatted_report,
            parse_mode="HTML",
        )
        notifications_logger.info("Successfully sent AoC leaderboard update")
    else:
        notifications_logger.info("AoC notification is turned off, skipping sending notifications")


async def handle_notification_for_course(context: ContextTypes.DEFAULT_TYPE):
    course_id: int = context.job.data["course_id"]
    if course_id == constants.ddia_5_course_id and not models.ddia_notification_on:
        notifications_logger.info("DDIA notification is turned off, skipping sending DDIA notification")
        return
    if course_id == constants.dmls_course_id and not models.dmls_notification_on:
        notifications_logger.info("DMLS notification is turned off, skipping sending DMLS notification")
        return
    current_week: int = datetime.date.today().isocalendar().week
    with (Session(engine) as session):
        try:
            call_link = session.query(ScheduledPartMessages.text) \
                .filter(
                    (ScheduledPartMessages.course_id == course_id) &
                    (ScheduledPartMessages.week_number == current_week)) \
                .one()[0]
        except NoResultFound as e:
            load_dotenv(override=True)
            admin_chat_id = int(os.getenv('ADMIN_CHAT_ID'))
            notifications_logger.debug(f"reloaded admin chat id: {admin_chat_id}")

            await context.bot.send_message(
                chat_id=admin_chat_id,
                text=f"Zoom link for {constants.id_to_course[course_id]} not found for today!"
            )
            notifications_logger.error('Zoom link for {constants.id_to_course[course_id]} not found for today!',
                                       exc_info=e)
            return

        notifications_logger.info(f'call_link is {call_link}')

    if call_link:
        context.job.data["message"] = f"{constants.before_call_reminders[course_id]}\n\n{call_link}"
    else:
        context.job.data["message"] = constants.before_call_reminders[course_id]
    await handle_notification(context)


async def prompt_to_connect_patreon_notifications(context: ContextTypes.DEFAULT_TYPE):
    # todo: don't hardcode things, move table links and buttons to constants
    course_id: int = context.job.data["course_id"]

    if course_id == constants.ddia_5_course_id and not models.ddia_notification_on:
        notifications_logger.info(f"Skipping a prompt to connect Patreon for course {constants.id_to_course[course_id]}"
                                  f" because DDIA is turned off")
        await context.bot.send_message(
            chat_id=settings.ADMIN_CHAT_ID,
            text=f"Skipping {constants.id_to_course[course_id]} prompt to connect Patreon because DDIA course is "
                 f"turned off",
            parse_mode="HTML")
        return

    if course_id == constants.dmls_course_id and not models.dmls_notification_on:
        notifications_logger.info(f"Skipping a prompt to connect Patreon for course {constants.id_to_course[course_id]}"
                                  f" because DMLS is turned off")
        await context.bot.send_message(
            chat_id=settings.ADMIN_CHAT_ID,
            text=f"Skipping {constants.id_to_course[course_id]} prompt to connect Patreon because DMLS course is "
                 f"turned off",
            parse_mode="HTML")
        return

    if not models.pro_courses_on:
        notifications_logger.info(f"Skipping a prompt to connect Patreon for course {constants.id_to_course[course_id]}"
                                  f" because PRO courses are turned off")
        await context.bot.send_message(
            chat_id=settings.ADMIN_CHAT_ID,
            text=f"Skipping {constants.id_to_course[course_id]} prompt to connect Patreon because PRO courses are "
                 f"turned off",
            parse_mode="HTML")
        return

    notifications_logger.debug(f"prompt_to_connect_patreon_notifications for {constants.id_to_course[course_id]}")

    if course_id == constants.ddia_5_course_id:
            message: str = ("Привет! Сегодня вечером будет звонок с обсуждением Designing Data-Intensive Applications. Тему "
                    "сегодняшнего звонка можешь посмотреть <a href='https://docs.google.com/spreadsheets/d/1Q1brVbkrS-PDNRrmigOVN_AF8yGGHslLsBzVumkv9-0/edit?usp=sharing'>здесь</a>. "
                    "\n\n<b>Обсуждение DDIA — это 💜Pro курс, и чтобы сегодня вечером тебе пришла ссылка на звонок, нужна 💜Pro подписка!</b>"
                    "\n\n1. Чтобы оформить Pro подписку, подпишись на донат в $15 в месяц на моем "
                    "<a href='https://www.patreon.com/c/LenaAnyusha'>Patreon</a>."
                    "\n\nНикому не говори почту, которая привязана к твоему Patreon аккаунту! Когда оформишь подписку на Patreon, "
                    "привяжи почту по кнопке ⬇️"
                    "\n\n2. Либо оформи подписку на 1500 рублей на мой <a href='https://boosty.to/lenaan'>Boosty</a> и привяжи почту по кнопке ⬇️"                    "\n\n3. Если возникнут какие-то сложности, напиши @lenka_colenka!"
                    "\n\n4. Ты можешь отписаться от новостей про DDIA, чтобы больше не получать уведомления.")
    elif course_id == constants.leetcode_grind_3_course_id:
        message: str = (
            "Привет! Сегодня вечером будет звонок с обсуждением задач из списка Leetcode-75! Тему "
            "сегодняшнего звонка можешь посмотреть <a href='https://docs.google.com/spreadsheets/d/1ddCs4c4km3qFeyzyvzuQn6a9lC_V5M2ocyT8w9ShBwg/edit?gid=0'>здесь</a>. "
            "\n\n<b>Обсуждение Leetcode Grind — это 💜Pro курс, и чтобы сегодня вечером тебе пришла ссылка на звонок, нужна 💜Pro подписка!</b>"
            "\n\n1. Чтобы оформить Pro подписку, подпишись на донат в $15 в месяц на моем "
            "<a href='https://www.patreon.com/c/LenaAnyusha'>Patreon</a>."
            "\n\nНикому не говори почту, которая привязана к твоему Patreon аккаунту! Когда оформишь подписку на Patreon, "
            "привяжи почту по кнопке ⬇️"
            "\n\n2. Либо оформи подписку на 1500 рублей на мой <a href='https://boosty.to/lenaan'>Boosty</a> и привяжи почту по кнопке ⬇️"
            "\n\n3. Если возникнут какие-то сложности, напиши @lenka_colenka!"
            "\n\n4. Ты можешь отписаться от новостей про Leetcode Grind, чтобы больше не получать уведомления.")
    elif course_id == constants.dmls_course_id:
        message: str = (
            "Привет! Сегодня вечером будет звонок с обсуждением <a href='https://www.oreilly.com/library/view/designing-machine-learning/9781098107956/'>Designing Machine Learning Systems</a>. "
            "Тему сегодняшнего звонка можешь посмотреть <a href='https://docs.google.com/spreadsheets/d/12ZfAfGceVuPZZoWbmHaSPcwe1mLTl9Jg9YONP7JkmsQ/edit?gid=0#gid=0'>в таблице</a>. "
            "\n\n<b>Обсуждение DMLS — это 💜Pro курс, и чтобы сегодня вечером тебе пришла ссылка на звонок, нужна 💜Pro подписка!</b>"
            "\n\n1. Чтобы оформить Pro подписку, подпишись на донат в $15 в месяц на моем "
            "<a href='https://www.patreon.com/c/LenaAnyusha'>Patreon</a>. "
            "\n\nНикому не говори почту, которая привязана к твоему Patreon аккаунту! Когда оформишь подписку на Patreon, "
            "привяжи почту по кнопке ⬇️"
            "\n\n2. Либо оформи подписку на 1500 рублей на мой <a href='https://boosty.to/lenaan'>Boosty</a> и привяжи почту по кнопке ⬇️"
            "\n\n3. Если возникнут какие-то сложности, напиши @lenka_colenka!"
            "\n\n4. Ты можешь отписаться от новостей про DMLS, чтобы больше не получать уведомления.")
    else:
        raise Exception("unsupported course id!")

    menu = InlineKeyboardMarkup([
        [InlineKeyboardButton("Привязать профиль Patreon", callback_data="connect_patreon")],
        [InlineKeyboardButton("Привязать профиль Boosty", callback_data="connect_boosty")],
        [InlineKeyboardButton(f"Перестать получать уведомления о {constants.id_to_course[course_id]}",
                              callback_data=f"unenroll:{course_id}")],
    ])

    with Session(engine) as session:
        result = session.query(Enrollment.tg_id).filter(Enrollment.course_id == course_id).all()
        notification_chat_ids = [item[0] for item in result]
    notifications_logger.debug(f"handling Patreon prompt for {constants.id_to_course[course_id]}, got "
                               f"{len(notification_chat_ids)} chat ids that are subscribed to the course")

    # only Basic subscribers will get a prompt to subscribe to Patreon
    notification_chat_ids = [tg_id for tg_id in notification_chat_ids
                             if membership.get_user_membership_info(tg_id).get_overall_level() == membership.basic]
    notifications_logger.debug(f"handling Patreon prompt for {constants.id_to_course[course_id]}, got "
                               f"{len(notification_chat_ids)} Basic subscribers to {constants.id_to_course[course_id]}")

    await notifications_helpers.do_send_notifications(context, notification_chat_ids, message, menu,
                                                      f"{constants.id_to_course[course_id]} Patreon prompt")

# no matter winter or summer time in Europe.
# In theory should work without restart when the time changes
berlin_tz = ZoneInfo("Europe/Berlin")


async def register_leetcode_notifications(app):
    app.job_queue.run_daily(
        callback=handle_leetcode_reminder,
        time=datetime.time(hour=17, minute=6, tzinfo=berlin_tz),
        days=(4,),  # 0 = Sunday, ..., 4 = Thursday
        name=f"leetcode_notification",
        data={
            "course_id": constants.leetcode_course_id,
            "message": constants.mock_leetcode_reminder,
            "menu": InlineKeyboardMarkup(
                [[InlineKeyboardButton("Записаться на моки!", callback_data="leetcode_register")]])
        }
    )


async def register_sre_notifications(app):
    app.job_queue.run_daily(
        callback=handle_sre_notification,
        time=datetime.time(hour=17, minute=55, tzinfo=berlin_tz),
        days=(2,),  # 0 = Sunday, 2 = Tuesday
        name=f"sre_notification",
        data={"course_id": constants.sre_course_id}
    )


async def register_ddia_prompt_to_connect_patreon_notifications(app):
    app.job_queue.run_daily(
        callback=prompt_to_connect_patreon_notifications,
        time=datetime.time(hour=9, minute=53, tzinfo=berlin_tz),  # morning before DDIA call
        days=(4,),  # 0 = Sunday, 4 = Thursday
        name=f"ddia_prompt_to_connect_patreon_notification",
        data={"course_id": constants.ddia_5_course_id}
    )


async def register_dmls_prompt_to_connect_patreon_notifications(app):
    app.job_queue.run_daily(
        callback=prompt_to_connect_patreon_notifications,
        time=datetime.time(hour=9, minute=53, tzinfo=berlin_tz),  # morning before DMLS call
        days=(2,),  # 0 = Sunday, 2 = Tuesday
        name=f"dmls_prompt_to_connect_patreon_notification",
        data={"course_id": constants.dmls_course_id}
    )


async def register_ddia_notifications(app):
    app.job_queue.run_daily(
        callback=handle_notification_for_course,
        time=datetime.time(hour=17, minute=53, tzinfo=berlin_tz),
        days=(4,),  # 0 = Sunday, 4 = Thursday
        name=f"ddia_notification",
        data={"course_id": constants.ddia_5_course_id}
    )


async def register_leetcode_grind_prompt_to_connect_patreon_notifications(app):
    app.job_queue.run_daily(
        callback=prompt_to_connect_patreon_notifications,
        time=datetime.time(hour=9, minute=55, tzinfo=berlin_tz),  # morning before Leetcode Grind call
        days=(1,),  # 0 = Sunday, 1 = Monday
        name=f"leetcode_grind_prompt_to_connect_patreon_notification",
        data={"course_id": constants.leetcode_grind_3_course_id}
    )


async def register_leetcode_grind_notifications(app):
    app.job_queue.run_daily(
        callback=handle_notification_for_course,
        time=datetime.time(hour=17, minute=53, tzinfo=berlin_tz),
        days=(1,),  # 0 = Sunday, 1 = Monday
        name=f"leetcode_grind_notification",
        data={"course_id": constants.leetcode_grind_3_course_id}
    )


async def register_codecrafters_notifications(app):
    app.job_queue.run_daily(
        callback=handle_codecrafters_notification,
        time=datetime.time(hour=17, minute=55, tzinfo=berlin_tz),
        days=(2,),  # 0 = Sunday, 2 = Tuesday
        name=f"codecrafters_notification",
        data={"course_id": constants.codecrafters_course_id}
    )


async def register_codecrafters_kafka_notifications(app):
    app.job_queue.run_daily(
        callback=handle_codecrafters_kafka_notification,
        time=datetime.time(hour=17, minute=55, tzinfo=berlin_tz),
        days=(3,),  # 0 = Sunday, 3 = Wednesday
        name=f"codecrafters_kafka_notification",
        data={"course_id": constants.codecrafters_kafka_course_id}
    )


async def register_aoc_notifications(app):
    # should not hit API more than once every 15 minutes. Daily is fine
    app.job_queue.run_daily(
        callback=handle_aoc_notification,
        time=datetime.time(hour=20, minute=20, tzinfo=berlin_tz),
        days=(0, 1, 2, 3, 4, 5, 6),  # 0 = Sunday
        name=f"aoc_notification",
        data={"course_id": constants.aoc_course_id}
    )


async def register_dmls_notifications(app):
    app.job_queue.run_daily(
        callback=handle_notification_for_course,
        time=datetime.time(hour=18, minute=53, tzinfo=berlin_tz),
        days=(2,),  # 0 = Sunday, 2 = Tuesday
        name=f"dmls_notification",
        data={"course_id": constants.dmls_course_id}
    )
