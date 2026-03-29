import datetime
import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import constants
import helpers
import models
from . import fetch_patrons, fetch_boosty_patrons

membership_logger = logging.getLogger(__name__)
membership_logger.setLevel(logging.INFO)


@dataclass(order=True)
class MembershipLevel:
    number: int  # this is to compare two levels and get max
    name: str
    description: str
    price_cents: int  # compare it with sum_of_entitled_tiers_amount_cents returned from Patreon


basic = MembershipLevel(
    number=1,
    name="Базовый",
    description="Уровень твоей подписки: 💙Базовый.\n\n"
                "Тебе доступны Random Coffee без ограничений и участие в бесплатных потоках. Посмотреть активные потоки"
                " можно командой /courses. \n\n"
                "Время от времени также проходят оффлайн-сходки в городах и появляются эксклюзивные вакансии!\n\n"
                "Чтобы улучшить подписку, сделай презентацию либо подпишись на "
                "<a href='https://boosty.to/lenaan'>Boosty</a> на 1500 рублей в месяц либо на "
                "<a href='https://www.patreon.com/c/LenaAnyusha'>Patreon</a> на $15 в месяц",
    price_cents=0
)

pro = MembershipLevel(
    number=2,
    name="Pro",
    description="Уровень твоей подписки: 💜Pro.\n\nТебе доступны участие во всех потоках без ограничений!\n\n"
                "Посмотреть активные потоки можно командой /courses.",
    price_cents=1500
)


# todo: add Gold level
# give them unlimited thank you power
# give them ability to vote for new books? (hmm i can't promise that we'll read it)
# give them some badge


@dataclass
class UserMembershipInfo:
    member_level_by_activity: MembershipLevel = basic
    member_level_by_activity_expiration: date = date(year=1970, month=1, day=1)
    patreon_email: str = ""
    sum_of_entitled_tiers_amount_cents: int = 0
    # Boosty email is optional. User is identified by Boosty user_id. But bot user should be able to reference anyway.
    # If Boosty email is missing, try to show Boosty name.
    boosty_user_id: str = ""  # internal implementation, end user doesn't need to know about this
    boosty_email: str = ""
    boosty_name: str = ""
    boosty_price: int = 0

    def get_patreon_level(self) -> MembershipLevel:
        patreon_level = basic
        if self.sum_of_entitled_tiers_amount_cents >= 1500:
            if self.patreon_email != "":
                patreon_level = pro
            else:
                raise Exception("sum_of_entitled_tiers_amount_cents non-zero while patreon email is missing!")
        return patreon_level

    def get_boosty_level(self) -> MembershipLevel:
        return pro if self.boosty_price >= 1500 else basic

    def get_activity_level(self) -> MembershipLevel:
        if self.member_level_by_activity == pro:
            if self.member_level_by_activity_expiration is None or self.member_level_by_activity_expiration >= datetime.datetime.now().date():
                return pro
        return basic

    def get_overall_level(self) -> MembershipLevel:
        return max(self.get_activity_level(), self.get_patreon_level(), self.get_boosty_level(),
                   key=lambda level: level.number)

    def repr_boosty_profile(self) -> str:
        if self.boosty_email:
            return self.boosty_email
        if self.boosty_name:
            return self.boosty_name
        return self.boosty_user_id

    def __repr__(self):
        return (f"Level by activity: {self.member_level_by_activity.name}\n"
                f"Member level by activity expiration: {self.member_level_by_activity_expiration}\n\n"
                f"Patreon email: {self.patreon_email}\n"
                f"Patreon currently entitled amount cents: {self.sum_of_entitled_tiers_amount_cents}\n\n"
                f"Boosty email: {self.boosty_email}\n"
                f"Boosty name: {self.boosty_name}\n"
                f"Boosty price: {self.boosty_price}")


def load_membership_by_activity(tg_id: int, tg_username: str = None) -> tuple[MembershipLevel, date]:
    membership_logger.debug(f"load_membership_by_activity triggered by {tg_username}")

    level_by_activity: MembershipLevel = basic
    level_by_activity_expiration: date = date(year=1970, month=1, day=1)

    with Session(models.engine) as session:
        result = (
            session.query(models.MembershipByActivity.expires_at)
            .filter(models.MembershipByActivity.tg_id == str(tg_id))
            .one_or_none()
        )
        if result:
            membership_logger.debug(f"Got member by activity for {tg_username if tg_username else tg_id} with "
                                    f"expiration at: {result}")
            level_by_activity = pro
            level_by_activity_expiration = result[0]
    return level_by_activity, level_by_activity_expiration


def load_patreon_membership(tg_id: int, tg_username: str = None) -> tuple[str, int]:
    membership_logger.debug(f"load_patreon_membership triggered by {tg_username}")

    patreon_email: str = ""
    sum_of_entitled_tiers_amount_cents: int = 0

    with Session(models.engine) as session:
        result = (
            session.query(models.PatreonLink.patreon_email)
            .filter(models.PatreonLink.tg_id == str(tg_id))
            .one_or_none()
        )
        if result:
            membership_logger.debug(f"Got patreon linking for user {tg_username if tg_username else tg_id} : {result}")
            patreon_email = result[0]

    if patreon_email != "":
        patreon_info = fetch_patrons.get_patron_by_email(patreon_email)
        if patreon_info:
            sum_of_entitled_tiers_amount_cents = int(patreon_info["sum_of_entitled_tiers_amount_cents"])
        else:
            membership_logger.warning(f"Patreon Linking exists in DB, but not in Redis for user "
                                      f"{tg_username if tg_username else tg_id}, patreon email is {patreon_email}")
    return patreon_email, sum_of_entitled_tiers_amount_cents


def load_boosty_membership(tg_id: int, tg_username: str = None) -> tuple[str, str, str, int]:
    membership_logger.debug(f"load_boosty_membership triggered by {tg_username}")

    boosty_user_id: str = ""
    boosty_email: str = ""
    boosty_name: str = ""
    boosty_price: int = 0

    with Session(models.engine) as session:
        result = (
            session.query(models.BoostyLink.boosty_user_id)
            .filter(models.BoostyLink.tg_id == str(tg_id))
            .one_or_none()
        )
        if result:
            membership_logger.debug(f"Got Boosty linking for user {tg_username if tg_username else tg_id} : {result}")
            boosty_user_id = result[0]

    if boosty_user_id != "":
        boosty_info = fetch_boosty_patrons.get_boosty_info(boosty_user_id)
        if boosty_info:
            boosty_email = boosty_info["email"]
            boosty_name = boosty_info["name"]
            boosty_price = int(boosty_info["price"])
        else:
            membership_logger.warning(f"Boosty Linking exists in DB, but not in Redis for user "
                                      f"{tg_username if tg_username else tg_id}, boosty id is {boosty_user_id}")
    return boosty_user_id, boosty_email, boosty_name, boosty_price


def get_user_membership_info(tg_id: int, tg_username: str = None) -> UserMembershipInfo:
    membership_logger.debug(f"get_user_membership_info triggered by {tg_username}")

    info = UserMembershipInfo()
    info.member_level_by_activity, info.member_level_by_activity_expiration = (
        load_membership_by_activity(tg_id, tg_username))

    info.patreon_email, info.sum_of_entitled_tiers_amount_cents = load_patreon_membership(tg_id, tg_username)

    info.boosty_user_id, info.boosty_email, info.boosty_name, info.boosty_price = (
        load_boosty_membership(tg_id, tg_username))

    return info


def is_course_pro(course_id: int):
    # todo: don't hardcode pro courses
    return ((course_id == constants.ddia_5_course_id) or (course_id == constants.leetcode_grind_3_course_id) or
            (course_id == constants.dmls_course_id))


async def reply_for_patreon_members(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                    membership_info: UserMembershipInfo) -> None:
    membership_logger.info(f"reply_for_patreon_members triggered by {helpers.get_user(update)}")

    msg: str = membership_info.get_overall_level().description
    msg += (f"\n\n • Привязанный профиль Patreon: {membership_info.patreon_email}. Ты донатишь "
            f"${membership_info.sum_of_entitled_tiers_amount_cents // 100}. Спасибо! ❤️")

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("Отвязать профиль Patreon", callback_data="disconnect_patreon"),
    ]])

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=msg,
        reply_markup=reply_markup,
    )


async def reply_for_boosty_members(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   membership_info: UserMembershipInfo) -> None:
    membership_logger.info(f"reply_for_boosty_members triggered by {helpers.get_user(update)}")

    msg: str = membership_info.get_overall_level().description
    msg += (f"\n\n • Привязанный профиль Boosty: {membership_info.repr_boosty_profile()}. Ты донатишь "
            f"{membership_info.boosty_price} рублей. Спасибо! ❤️")

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("Отвязать профиль Boosty", callback_data="disconnect_boosty"),
    ]])

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=msg,
        reply_markup=reply_markup,
    )


async def reply_for_activity_members(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     membership_info: UserMembershipInfo) -> None:
    membership_logger.info(f"reply_for_activity_members triggered by {helpers.get_user(update)}")

    msg: str = membership_info.get_overall_level().description
    if not membership_info.member_level_by_activity_expiration:
        msg += f"\n\nУ тебя вечная подписка за активное участие в клубе!"
    else:
        if membership_info.member_level_by_activity_expiration < date.today():
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

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=msg,
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML"
    )


def get_patreon_reply(update: Update, membership_info: UserMembershipInfo) -> tuple[str, Optional[InlineKeyboardButton]]:
    if membership_info.patreon_email == "":
        membership_logger.debug(f"{helpers.repr_user_from_update(update)} doesn't have Patreon connected")
        return "", InlineKeyboardButton("Привязать профиль Patreon", callback_data="connect_patreon")
    else:
        msg = f"\n\n • Привязанный профиль Patreon: {membership_info.patreon_email}."
        if membership_info.sum_of_entitled_tiers_amount_cents > 0:
            msg += f" Ты донатишь ${membership_info.sum_of_entitled_tiers_amount_cents // 100}. Спасибо! ❤️"
        else:
            msg += f" Ты не донатишь мне на Patreon️"
        membership_logger.debug(f"{helpers.repr_user_from_update(update)} has Patreon connected")
        return msg, InlineKeyboardButton("Отвязать профиль Patreon", callback_data="disconnect_patreon")


def get_boosty_reply(update: Update, membership_info: UserMembershipInfo) -> tuple[str, Optional[InlineKeyboardButton]]:
    if membership_info.boosty_user_id == "":
        membership_logger.debug(f"{helpers.repr_user_from_update(update)} doesn't have Boosty connected")
        return "", InlineKeyboardButton("Привязать профиль Boosty", callback_data="connect_boosty")
    else:
        msg = f"\n\n • Привязанный профиль Boosty: {membership_info.repr_boosty_profile()}."
        if membership_info.boosty_price > 0:
            msg += f" Ты донатишь {membership_info.boosty_price} рублей. Спасибо! ❤️"
        else:
            msg += f" Ты не донатишь мне на Boosty"
        membership_logger.debug(f"{helpers.repr_user_from_update(update)} has Boosty connected")
        return msg, InlineKeyboardButton("Отвязать профиль Boosty", callback_data="disconnect_boosty")


async def handle_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = helpers.get_user(update)
    membership_logger.info(f"handle_membership triggered by {tg_user}")

    membership_info = get_user_membership_info(tg_user.id, tg_user.username)

    if membership_info.get_patreon_level() == pro:
        await reply_for_patreon_members(update, context, membership_info)
        return

    if membership_info.get_boosty_level() == pro:
        await reply_for_boosty_members(update, context, membership_info)
        return

    if membership_info.member_level_by_activity == pro:
        await reply_for_activity_members(update, context, membership_info)
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

    membership_logger.info(f"{helpers.repr_user_from_update(update)} has {membership_info.get_overall_level().name} "
                           f"subscription")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=msg,
        reply_markup=InlineKeyboardMarkup(menu),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
