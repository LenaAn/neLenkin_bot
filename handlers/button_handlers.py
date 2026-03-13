import datetime
import logging
from typing import Optional

from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, User
from telegram.ext import ContextTypes

import constants
import helpers
import membership
import models
from handlers import boosty_handlers, patreon_handlers
import settings


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    handlers_dict = {
        "back": handle_back_to_start,
        "how_to_join": handle_how_to_join,
        "course_info": handle_course_info,
        "back_to_ddia": handle_back_to_ddia,
        "enroll": handle_enroll,
        "unenroll": handle_unenroll,
        "how_to_present": handle_how_to_present,
        "membership": handle_membership,
        "disconnect_patreon": patreon_handlers.disconnect_patreon_handler,
        "disconnect_boosty": boosty_handlers.disconnect_boosty_handler,
    }

    command: str = query.data
    if ":" in query.data:
        context.user_data["callback_course_id"] = int(query.data.split(":")[1])
        command = query.data.split(":")[0]

    handler = handlers_dict.get(command)
    if handler:
        await handler(update, context)
    else:
        logging.warning(f"Unhandled callback query data: {command} by {helpers.repr_user_from_update(update)}")


async def handle_back_to_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"back_to_start triggered by {helpers.repr_user_from_update(update)}")
    await update.callback_query.edit_message_text(
        text=constants.club_description,
        reply_markup=helpers.main_menu()
    )


async def handle_how_to_join(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"how_to_join triggered by {helpers.repr_user_from_update(update)}")
    await update.callback_query.edit_message_text(
        text=constants.how_to_join_description,
        reply_markup=helpers.join_menu())


async def handle_back_to_ddia(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"back_to_ddia triggered by {helpers.repr_user_from_update(update)}")
    await handle_course_info(update, constants.ddia_4_course_id)


def user_is_enrolled(tg_user: User, course_id: int) -> bool:
    with Session(models.engine) as session:
        users_exists = session.scalar(
            select(exists().where(
                (models.Enrollment.tg_id == str(tg_user.id)) & (models.Enrollment.course_id == course_id))
            )
        )
    if users_exists:
        logging.info(f"user is already enrolled in {constants.id_to_course[course_id]}: {helpers.repr_user(tg_user)}")
    else:
        logging.info(
            f"user is not already enrolled in {constants.id_to_course[course_id]}: {helpers.repr_user(tg_user)}")
    return users_exists


async def handle_course_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    course_id = context.user_data["callback_course_id"]
    del context.user_data["callback_course_id"]
    logging.info(f"handle_course_info for {constants.id_to_course[course_id]} triggered by "
                 f"{helpers.repr_user_from_update(update)}")

    tg_user = helpers.get_user(update)
    if user_is_enrolled(tg_user, course_id):
        button_list = [
            InlineKeyboardButton("Перестать получать уведомления", callback_data=f"unenroll:{course_id}"),
            InlineKeyboardButton("Назад", callback_data="back"),
        ]
        menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
        await update.callback_query.edit_message_text(
            text=constants.id_to_description[course_id] + "\n\n" + constants.id_to_enroll_description[course_id],
            reply_markup=InlineKeyboardMarkup(menu),
            parse_mode="HTML")
    else:
        button_list = [
            InlineKeyboardButton("Хочу участвовать!", callback_data=f"enroll:{course_id}"),
            InlineKeyboardButton("Назад", callback_data="back"),
        ]
        menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
        await update.callback_query.edit_message_text(
            text=constants.id_to_description[course_id] + "\n\n" + constants.id_to_cta[course_id],
            reply_markup=InlineKeyboardMarkup(menu),
            parse_mode="HTML")


async def reply_for_patreon_members(update: Update, membership_info: membership.UserMembershipInfo) -> None:
    logging.info(f"reply_for_patreon_members triggered by {helpers.get_user(update)}")

    msg: str = membership_info.get_overall_level().description
    msg += (f"\n\n • Привязанный профиль Patreon: {membership_info.patreon_email}. Ты донатишь "
            f"${membership_info.sum_of_entitled_tiers_amount_cents // 100}. Спасибо! ❤️")

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("Отвязать профиль Patreon", callback_data="disconnect_patreon"),
    ]])

    await update.callback_query.edit_message_text(
        text=msg,
        reply_markup=reply_markup,
    )


async def reply_for_boosty_members(update: Update, membership_info: membership.UserMembershipInfo) -> None:
    logging.info(f"reply_for_boosty_members triggered by {helpers.get_user(update)}")

    msg: str = membership_info.get_overall_level().description
    msg += (f"\n\n • Привязанный профиль Boosty: {membership_info.repr_boosty_profile()}. Ты донатишь "
            f"{membership_info.boosty_price} рублей. Спасибо! ❤️")

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("Отвязать профиль Boosty", callback_data="disconnect_boosty"),
    ]])
    await update.callback_query.edit_message_text(
        text=msg,
        reply_markup=reply_markup,
    )


async def reply_for_activity_members(update: Update, membership_info: membership.UserMembershipInfo) -> None:
    logging.info(f"reply_for_activity_members triggered by {helpers.get_user(update)}")

    msg: str = membership_info.get_overall_level().description
    if not membership_info.member_level_by_activity_expiration:
        msg += f"\n\nУ тебя вечная подписка за активное участие в клубе!"
    else:
        if membership_info.member_level_by_activity_expiration < datetime.date.today():
            msg += f"\n\nТвоя подписка за активное участие закончилась :("
        else:
            msg += (f"\n\nТвоя подписка за активное участие истечет "
                    f"{membership_info.member_level_by_activity_expiration}."
                    f"\n\nЧтобы сохранить 💜Pro подписку, сделай презентацию либо подпишись на "
                    f"<a href='https://www.patreon.com/c/LenaAnyusha'>Patreon</a> хотя бы на $15 в месяц.\n\n")

    buttons = []
    if membership_info.patreon_email == "":
        buttons.append(InlineKeyboardButton("Привязать профиль Patreon", callback_data="connect_patreon"))
    else:
        buttons.append(InlineKeyboardButton("Отвязать профиль Patreon", callback_data="disconnect_patreon"))

    if membership_info.boosty_user_id == "":
        buttons.append(InlineKeyboardButton("Привязать профиль Boosty", callback_data="connect_boosty"))
    else:
        buttons.append(InlineKeyboardButton("Отвязать профиль Boosty", callback_data="disconnect_boosty"))
    menu = [buttons[i:i + 1] for i in range(0, len(buttons), 1)]

    await update.callback_query.edit_message_text(
        text=msg,
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML"
    )


async def reply_for_basic(update: Update, membership_info: membership.UserMembershipInfo) -> None:
    logging.info(f"reply_for_basic triggered by {helpers.get_user(update)}")

    msg: str = membership_info.get_overall_level().description
    msg += ("\n\nЧтобы улучшить подписку, сделай презентацию либо подпишись на "
            "<a href='https://www.patreon.com/c/LenaAnyusha'>Patreon</a> хотя бы на $15 в месяц")
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Привязать профиль Patreon", callback_data="connect_patreon")],
        [InlineKeyboardButton("Привязать профиль Boosty", callback_data="connect_boosty")],
    ])
    await update.callback_query.edit_message_text(
        text=msg,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )


def get_patreon_reply(update: Update, membership_info: membership.UserMembershipInfo) -> tuple[str, Optional[InlineKeyboardButton]]:
    logging.info(f"get_patreon_reply triggered by {helpers.get_user(update)}")
    if membership_info.patreon_email == "":
        return "", InlineKeyboardButton("Привязать профиль Patreon", callback_data="connect_patreon")
    else:
        msg = f"\n\n • Привязанный профиль Patreon: {membership_info.patreon_email}."
        if membership_info.sum_of_entitled_tiers_amount_cents > 0:
            msg += f" Ты донатишь ${membership_info.sum_of_entitled_tiers_amount_cents // 100}. Спасибо! ❤️"
        else:
            msg += f" Ты не донатишь мне на Patreon️"
        return msg, InlineKeyboardButton("Отвязать профиль Patreon", callback_data="disconnect_patreon")


def get_boosty_reply(update: Update, membership_info: membership.UserMembershipInfo) -> tuple[str, Optional[InlineKeyboardButton]]:
    logging.info(f"get_boosty_reply triggered by {helpers.get_user(update)}")

    if membership_info.boosty_user_id == "":
        return "", InlineKeyboardButton("Привязать профиль Boosty", callback_data="connect_boosty")
    else:
        msg = f"\n\n • Привязанный профиль Boosty: {membership_info.repr_boosty_profile()}."
        if membership_info.boosty_price > 0:
            msg += f" Ты донатишь {membership_info.boosty_price} рублей. Спасибо! ❤️"
        else:
            msg += f" Ты не донатишь мне на Boosty"
        return msg, InlineKeyboardButton("Отвязать профиль Boosty", callback_data="disconnect_boosty")


async def handle_membership(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = helpers.get_user(update)
    logging.info(f"handle_membership triggered by {tg_user}")

    membership_info = membership.get_user_membership_info(tg_user.id, tg_user.username)

    if membership_info.get_patreon_level() == membership.pro:
        await reply_for_patreon_members(update, membership_info)
        return

    if membership_info.get_boosty_level() == membership.pro:
        await reply_for_boosty_members(update, membership_info)
        return

    if membership_info.member_level_by_activity == membership.pro:
        await reply_for_activity_members(update, membership_info)
        return

    # otherwise user has basic level
    # they may have 1 of 4 options:
    # 1. No Accounts Connected -> Show them two buttons
    # 2. Only Patreon Connected (but not enough money donating) -> Show then how much they are donating, don't mention Boosty
    # 3. Only Boosty Connected (but not enough money donating) -> Show them how much they are donating, don't mention Patreon
    # 4. Both Boosty and Patreon Connected -> Shouldn't happen, but can happen since not enforced on DB level. Show both and add buttons to unlink any of this

    msg: str = membership_info.get_overall_level().description
    patreon_message, patreon_button = get_patreon_reply(update, membership_info)
    boosty_message, boosty_button = get_boosty_reply(update, membership_info)

    msg += patreon_message
    msg += boosty_message

    button_list = []
    if patreon_button:
        button_list.append(patreon_button)
    if boosty_button:
        button_list.append(boosty_button)
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]

    await update.callback_query.edit_message_text(
        text=msg,
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    return


async def handle_enroll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    course_id = context.user_data["callback_course_id"]
    del context.user_data["callback_course_id"]
    logging.info(f"enroll for {constants.id_to_course[course_id]} handled by {helpers.repr_user_from_update(update)}")

    tg_user = helpers.get_user(update)
    with Session(models.engine) as session:
        enrollment = models.Enrollment(
            course_id=course_id,
            tg_id=tg_user.id
        )
        session.add(enrollment)
        try:
            session.commit()
            logging.info(f"Add user enrollment to {constants.id_to_course[course_id]} to db: "
                         f"{helpers.repr_user(tg_user)}")
        except IntegrityError as e:
            session.rollback()
            logging.info(f"Didn't add user {helpers.repr_user(tg_user)} enrollment to "
                         f"{constants.id_to_course[course_id]} to db: {e}")
        except Exception as e:
            session.rollback()
            logging.warning(f"Couldn't add user enrollment to {constants.id_to_course[course_id]}: {e}")
    button_list = [
        InlineKeyboardButton("Перестать получать уведомления", callback_data=f"unenroll:{course_id}"),
        InlineKeyboardButton("Назад", callback_data="back"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    await update.callback_query.edit_message_text(
        text=constants.id_to_enroll_description[course_id],
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML"
    )


async def handle_unenroll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    course_id = context.user_data["callback_course_id"]
    del context.user_data["callback_course_id"]
    logging.info(f"unenroll for {constants.id_to_course[course_id]} handled by {helpers.repr_user_from_update(update)}")

    tg_user = helpers.get_user(update)
    with Session(models.engine) as session:
        try:
            session.query(models.Enrollment).filter(
                (models.Enrollment.tg_id == str(tg_user.id)) & (models.Enrollment.course_id == course_id)).delete()
            session.commit()
            logging.info(f"Deleted user enrollment to {constants.id_to_course[course_id]} from db: "
                         f"{helpers.repr_user(tg_user)}")
        except Exception as e:
            session.rollback()
            logging.error(f"Couldn't delete user enrollment to {constants.id_to_course[course_id]}: {e}")
            raise e  # to propagate it to error handler

    button_list = [
        InlineKeyboardButton("Назад", callback_data="back"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    await update.callback_query.edit_message_text(
        text=constants.id_to_unenroll_description[course_id],
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML"
    )


async def handle_how_to_present(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f"how_to_present triggered by {helpers.repr_user_from_update(update)}")
    button_list = [
        InlineKeyboardButton("Назад", callback_data="back_to_ddia"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    await update.callback_query.edit_message_text(
        text=constants.how_to_present_description,
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    # todo: ignore "Message is not modified" and "Query is too old" errors?
    if not isinstance(update, Update):
        logging.info(f"error with invalid update")
    else:
        logging.info(f"error triggered by {update}", exc_info=context.error)
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=constants.error_description,
                parse_mode="HTML")
        except Exception as e:
            logging.info(f"couldn't send error message to user", exc_info=e)

        try:
            await context.bot.send_message(
                chat_id=settings.ADMIN_CHAT_ID,
                text=f"error triggered by {helpers.get_user(update)}: {context.error}",
                parse_mode="HTML")
        except Exception as e:
            logging.error(f"couldn't send error message to admin", exc_info=e)
