import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.orm import Session

import models
from membership import convert_points_to_membership, membership


@pytest.mark.asyncio
async def test_points_conversion_grants_membership_to_basic_members_only(
    test_db, monkeypatch
):
    with Session(test_db) as session:
        session.add_all(
            [
                models.User(tg_id="101", tg_username="basic"),
                models.User(tg_id="102", tg_username="pro"),
                models.User(tg_id="103", tg_username="below-threshold"),
            ]
        )
        session.add_all(
            [
                models.ClubPoints(tg_id="101", balance=1200),
                models.ClubPoints(tg_id="102", balance=1500),
                models.ClubPoints(tg_id="103", balance=999),
            ]
        )
        session.commit()

    monkeypatch.setattr(
        convert_points_to_membership.fetch_boosty_patrons,
        "load_boosty_patrons",
        AsyncMock(),
    )
    monkeypatch.setattr(
        convert_points_to_membership.fetch_patrons, "load_patrons", AsyncMock()
    )
    levels = {"101": membership.basic, "102": membership.pro}
    monkeypatch.setattr(
        convert_points_to_membership.membership,
        "get_user_membership_info",
        lambda tg_id: SimpleNamespace(get_overall_level=lambda: levels[tg_id]),
    )
    bot = SimpleNamespace(send_message=AsyncMock())

    await convert_points_to_membership.do_convert_points_to_membership(
        SimpleNamespace(bot=bot)
    )

    with Session(test_db) as session:
        balances = {
            row.tg_id: row.balance for row in session.query(models.ClubPoints).all()
        }
        expiry = (
            session.query(models.MembershipByActivity.expires_at)
            .filter_by(tg_id="101")
            .one()[0]
        )

    assert balances == {"101": 200, "102": 1500, "103": 999}
    assert expiry == datetime.date.today() + datetime.timedelta(days=31)
    assert bot.send_message.await_count == 2
    assert (
        bot.send_message.await_args_list[0].kwargs["chat_id"]
        == convert_points_to_membership.settings.ADMIN_CHAT_ID
    )
    assert bot.send_message.await_args_list[1].kwargs["chat_id"] == "101"
    assert "Текущий баланс: 200" in bot.send_message.await_args_list[1].kwargs["text"]
