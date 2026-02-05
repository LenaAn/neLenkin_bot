import logging
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

import constants
import models
from patreon import fetch_patrons, fetch_boosty_patrons


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
                "Тебе доступны Random Coffee без ограничений и участие в бесплатных потоках. "
                "Время от времени также проходят оффлайн-сходки в городах и появляются эксклюзивные вакансии!\n\n"
                "Чтобы улучшить подписку, сделай презентацию либо подпишись на "
                "<a href='https://boosty.to/lenaan'>Boosty</a> на 1500 рублей в месяц либо на "
                "<a href='https://www.patreon.com/c/LenaAnyusha'>Patreon</a> на $15 в месяц",
    price_cents=0
)

pro = MembershipLevel(
    number=2,
    name="Pro",
    description="Уровень твоей подписки: 💜Pro.\n\nТебе доступны участие во всех потоках без ограничений!",
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

    def get_overall_level(self) -> MembershipLevel:
        return max(self.member_level_by_activity, self.get_patreon_level(), self.get_boosty_level(),
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
    logging.info(f"load_membership_by_activity triggered by {tg_username}")

    level_by_activity: MembershipLevel = basic
    level_by_activity_expiration: date = date(year=1970, month=1, day=1)

    with Session(models.engine) as session:
        result = (
            session.query(models.MembershipByActivity.expires_at)
            .filter(models.MembershipByActivity.tg_id == str(tg_id))
            .one_or_none()
        )
        if result:
            logging.info(f"Got member by activity for {tg_username if tg_username else tg_id} with expiration at: {result}")
            level_by_activity = pro
            level_by_activity_expiration = result[0]
    return level_by_activity, level_by_activity_expiration


def load_patreon_membership(tg_id: int, tg_username: str = None) -> tuple[str, int]:
    logging.info(f"load_patreon_membership triggered by {tg_username}")

    patreon_email: str = ""
    sum_of_entitled_tiers_amount_cents: int = 0

    with Session(models.engine) as session:
        result = (
            session.query(models.PatreonLink.patreon_email)
            .filter(models.PatreonLink.tg_id == str(tg_id))
            .one_or_none()
        )
        if result:
            logging.info(f"Got patreon linking for user {tg_username if tg_username else tg_id} : {result}")
            patreon_email = result[0]

    if patreon_email != "":
        patreon_info = fetch_patrons.get_patron_by_email(patreon_email)
        if patreon_info:
            sum_of_entitled_tiers_amount_cents = int(patreon_info["sum_of_entitled_tiers_amount_cents"])
        else:
            logging.warning(f"Patreon Linking exists in DB, but not in Redis for user "
                            f"{tg_username if tg_username else tg_id}, patreon email is {patreon_email}")
    return patreon_email, sum_of_entitled_tiers_amount_cents


def load_boosty_membership(tg_id: int, tg_username: str = None) -> tuple[str, str, str, int]:
    logging.info(f"load_boosty_membership triggered by {tg_username}")

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
            logging.info(f"Got Boosty linking for user {tg_username if tg_username else tg_id} : {result}")
            boosty_user_id = result[0]

    if boosty_user_id != "":
        boosty_info = fetch_boosty_patrons.get_boosty_info(boosty_user_id)
        if boosty_info:
            boosty_email = boosty_info["email"]
            boosty_name = boosty_info["name"]
            boosty_price = int(boosty_info["price"])
        else:
            logging.warning(f"Boosty Linking exists in DB, but not in Redis for user "
                            f"{tg_username if tg_username else tg_id}, boosty id is {boosty_user_id}")
    return boosty_user_id, boosty_email, boosty_name, boosty_price


def get_user_membership_info(tg_id: int, tg_username: str = None) -> UserMembershipInfo:
    logging.info(f"get_user_membership_info triggered by {tg_username}")

    info = UserMembershipInfo()
    info.member_level_by_activity, info.member_level_by_activity_expiration = (
        load_membership_by_activity(tg_id, tg_username))

    info.patreon_email, info.sum_of_entitled_tiers_amount_cents = load_patreon_membership(tg_id, tg_username)

    info.boosty_user_id, info.boosty_email, info.boosty_name, info.boosty_price = (
        load_boosty_membership(tg_id, tg_username))

    return info


def is_course_pro(course_id: int):
    # todo: don't hardcode pro courses
    return (course_id == constants.ddia_4_course_id) or (course_id == constants.grind_course_id)
