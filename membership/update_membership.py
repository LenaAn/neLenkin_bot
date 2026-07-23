import datetime
import logging

import sqlalchemy
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

import models


def do_add_days(tg_id: str, days_count: int) -> tuple[int, datetime.date | None]:
    with (Session(models.engine) as session):
        existing = session.query(models.MembershipByActivity).filter(models.MembershipByActivity.tg_id == tg_id).first()
        if existing and not existing.expires_at:
            logging.info(f"User {tg_id} has infinite membership by activity, no days added")
            return 0, None

        if existing and existing.expires_at > datetime.date.today():
            current_expiry = existing.expires_at
        else:
            current_expiry = datetime.date.today()

        # todo: will break with concurrent updates in the following scenario:
        # both clients read the old value, update it in their process and write a new value
        new_expiry = current_expiry + datetime.timedelta(days=days_count)

        if existing:
            stmt = (sqlalchemy.update(models.MembershipByActivity)
                    .where(models.MembershipByActivity.tg_id == tg_id)
                    .values(expires_at=new_expiry))
        else:
            stmt = (
                sqlalchemy.insert(models.MembershipByActivity)
                .values(
                    tg_id=tg_id,
                    expires_at=new_expiry,
                )
            )

        session.execute(stmt)
        session.commit()
        logging.info(f"new membership expiry for {tg_id}: {new_expiry}")
        return days_count, new_expiry


def do_add_points(tg_id: int, point_count: int) -> tuple[int, int]:
    with (Session(models.engine) as session):
        stmt = insert(models.ClubPoints).values(tg_id=tg_id, balance=point_count)
        stmt = stmt.on_conflict_do_update(
            index_elements=[models.ClubPoints.tg_id],
            set_={"balance": models.ClubPoints.balance + point_count}
        ).returning(models.ClubPoints.balance)

        new_balance = session.execute(stmt).scalar_one()
        session.commit()
        logging.info(f"new Club Points balance for {tg_id}: {new_balance}")
    return point_count, new_balance
