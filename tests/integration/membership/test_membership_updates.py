import datetime

from sqlalchemy.orm import Session

import models
from membership import update_membership


def test_add_days_creates_and_extends_membership(test_db):
    with Session(test_db) as session:
        session.add(models.User(tg_id="101"))
        session.commit()
    count, expiry = update_membership.do_add_days("101", 31)
    assert count == 31
    assert expiry == datetime.date.today() + datetime.timedelta(days=31)
    count, extended = update_membership.do_add_days("101", 10)
    assert count == 10
    assert extended == expiry + datetime.timedelta(days=10)


def test_add_days_restarts_expired_membership_from_today(test_db):
    with Session(test_db) as session:
        session.add(models.User(tg_id="101"))
        session.flush()
        session.add(
            models.MembershipByActivity(
                tg_id="101",
                expires_at=datetime.date.today() - datetime.timedelta(days=2),
            )
        )
        session.commit()
    _, expiry = update_membership.do_add_days("101", 7)
    assert expiry == datetime.date.today() + datetime.timedelta(days=7)


def test_add_days_does_not_change_infinite_membership(test_db):
    with Session(test_db) as session:
        session.add(models.User(tg_id="101"))
        session.flush()
        session.add(models.MembershipByActivity(tg_id="101", expires_at=None))
        session.commit()
    assert update_membership.do_add_days("101", 7) == (0, None)


def test_add_and_subtract_points(test_db):
    assert update_membership.do_add_points(101, 200) == (200, 200)
    assert update_membership.do_add_points(101, 50) == (50, 250)
    # The database stores Telegram IDs as text, matching the update query's comparison type.
    assert update_membership.do_substract_points("101", 100) == (100, 150)
    assert update_membership.do_substract_points("999", 100) == (0, None)
