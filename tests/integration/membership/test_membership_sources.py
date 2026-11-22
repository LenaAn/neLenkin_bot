import datetime

from sqlalchemy.orm import Session

import models
from membership import membership


def test_user_membership_combines_activity_patreon_and_boosty_sources(
    test_db, monkeypatch
):
    today = datetime.date.today()
    with Session(test_db) as session:
        session.add_all(
            [
                models.User(tg_id="101"),
                models.User(tg_id="102"),
                models.User(tg_id="103"),
                models.User(tg_id="104"),
                models.User(tg_id="105"),
            ]
        )
        session.flush()
        session.add_all(
            [
                models.MembershipByActivity(tg_id="101", expires_at=today),
                models.MembershipByActivity(
                    tg_id="102", expires_at=today - datetime.timedelta(days=1)
                ),
                models.PatreonLink(tg_id="103", patreon_email="patreon@example.test"),
                models.BoostyLink(tg_id="104", boosty_user_id="boosty-user"),
            ]
        )
        session.commit()

    monkeypatch.setattr(
        membership.fetch_patrons,
        "get_patron_by_email",
        lambda email: {"sum_of_entitled_tiers_amount_cents": "1500"},
    )
    monkeypatch.setattr(
        membership.fetch_boosty_patrons,
        "get_boosty_info",
        lambda user_id: {"email": "", "name": "Boosty member", "price": "1500"},
    )

    assert (
        membership.get_user_membership_info(101).get_overall_level() == membership.pro
    )
    assert (
        membership.get_user_membership_info(102).get_overall_level() == membership.basic
    )
    assert (
        membership.get_user_membership_info(103).get_overall_level() == membership.pro
    )
    assert (
        membership.get_user_membership_info(104).get_overall_level() == membership.pro
    )
    assert (
        membership.get_user_membership_info(105).get_overall_level() == membership.basic
    )
