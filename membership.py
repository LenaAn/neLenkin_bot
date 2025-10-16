from dataclasses import dataclass


@dataclass(order=True)
class MembershipLevel:
    level: int  # this is to compare two levels and get max
    name: str
    description: str
    price_cents: int  # compare it with currently_entitled_amount_cents returned from Patreon


basic = MembershipLevel(
    level=1,
    name="Базовый",
    description="Уровень твоей подписки: 💙Базовый.\n\nТебе доступны Random Coffee без ограничений и участие в "
                "бесплатных потоках. Время от времени также проходят оффлайн-сходки в городах и "
                "появляются эксклюзивные вакансии!",
    price_cents=0
)

standard = MembershipLevel(
    level=2,
    name="Стандартный",
    description="Уровень твоей подписки: 💜Стандартный.\n\nТебе доступны участие во всех потоках без ограничений!",
    price_cents=1500
)

# todo: add Gold level
# give them unlimited thank you power
# give them ability to vote for new books? (hmm i can't promise that we'll read it)
# give them some badge


def get_level_from_patreon_info(patreon_info: dict) -> MembershipLevel:
    # todo: iterate (or bin search, if there are too many) over membership levels and compare to their price_cents
    if int(patreon_info['currently_entitled_amount_cents']) >= 1500:
        return standard
    else:
        return basic
