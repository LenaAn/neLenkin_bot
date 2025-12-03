import logging
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session
from telegram import User

import constants
import models
from patreon import fetch_patrons


@dataclass(order=True)
class MembershipLevel:
    number: int  # this is to compare two levels and get max
    name: str
    description: str
    price_cents: int  # compare it with currently_entitled_amount_cents returned from Patreon


basic = MembershipLevel(
    number=1,
    name="Базовый",
    description="Уровень твоей подписки: 💙Базовый.\n\nТебе доступны Random Coffee без ограничений и участие в "
                "бесплатных потоках. Время от времени также проходят оффлайн-сходки в городах и "
                "появляются эксклюзивные вакансии!",
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
    patreon_currently_entitled_amount_cents: int = 0

    def get_patreon_level(self) -> MembershipLevel:
        patreon_level = basic
        if self.patreon_currently_entitled_amount_cents >= 1500:
            if self.patreon_email != "":
                patreon_level = pro
            else:
                raise Exception("patreon_currently_entitled_amount_cents non-zero while patreon email is missing!")
        return patreon_level

    def get_overall_level(self) -> MembershipLevel:
        return max(self.member_level_by_activity, self.get_patreon_level(), key=lambda level: level.number)

    def __repr__(self):
        return (f"Level by activity: {self.member_level_by_activity.name}\n"
                f"Member level by activity expiration: {self.member_level_by_activity_expiration}\n"
                f"Patreon email: {self.patreon_email}\n"
                f"Patreon currently entitled amount cents: {self.patreon_currently_entitled_amount_cents}")


def get_user_membership_info(tg_id: int, tg_username: str = None) -> UserMembershipInfo:
    if tg_username is None:
        tg_username = tg_id

    info = UserMembershipInfo()

    with Session(models.engine) as session:
        result = (
            session.query(models.MembershipByActivity.expires_at)
            .filter(models.MembershipByActivity.tg_id == str(tg_id))
            .one_or_none()
        )
        if result:
            logging.info(f"Got member by activity for {tg_username} with expiration at: {result}")
            info.member_level_by_activity = pro
            info.member_level_by_activity_expiration = result[0]
        else:
            info.member_level_by_activity = basic

    with Session(models.engine) as session:
        result = (
            session.query(models.PatreonLink.patreon_email)
            .filter(models.PatreonLink.tg_id == str(tg_id))
            .one_or_none()
        )
        if result:
            logging.info(f"Got patreon linking for user {tg_username}: {result}")
            info.patreon_email = result[0]

    if info.patreon_email != "":
        patreon_info = fetch_patrons.get_patron_by_email(info.patreon_email)
        if patreon_info:
            info.patreon_currently_entitled_amount_cents = int(patreon_info["currently_entitled_amount_cents"])
        else:
            info.patreon_currently_entitled_amount_cents = 0
            logging.warning(f"Patreon Linking exists in DB, but not in Redis for user {tg_username}, patreon email"
                            f" is {info.patreon_email}")

    return info


def is_course_pro(course_id: int):
    # todo: don't hardcode pro courses
    return (course_id == constants.ddia_4_course_id) or (course_id == constants.grind_course_id)
