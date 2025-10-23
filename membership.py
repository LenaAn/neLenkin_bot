import logging
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session
from telegram import User

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

standard = MembershipLevel(
    number=2,
    name="Стандартный",
    description="Уровень твоей подписки: 💜Стандартный.\n\nТебе доступны участие во всех потоках без ограничений!",
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

    def get_overall_level(self) -> MembershipLevel:
        patreon_level = basic
        if self.patreon_currently_entitled_amount_cents >= 1500:
            if self.patreon_email != "":
                patreon_level = standard
            else:
                raise Exception("patreon_currently_entitled_amount_cents non-zero while patreon email is missing!")
        return max(self.member_level_by_activity, patreon_level, key=lambda level: level.number)


def get_user_membership_info(tg_user: User) -> UserMembershipInfo:
    info = UserMembershipInfo()

    # todo: lookup in DB for by_activity

    with Session(models.engine) as session:
        result = (
            session.query(models.PatreonLink.patreon_email)
            .filter(models.PatreonLink.tg_id == str(tg_user.id))
            .one_or_none()
        )
        if result:
            logging.info(f"Got patreon linking for user {tg_user.username}: {result}")
            info.patreon_email = result[0]

    if info.patreon_email != "":
        patreon_info = fetch_patrons.get_patron_by_email(info.patreon_email)
        info.patreon_currently_entitled_amount_cents = int(patreon_info["currently_entitled_amount_cents"])

    return info
