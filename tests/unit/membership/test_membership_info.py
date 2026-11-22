import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from membership import membership


@pytest.mark.parametrize(
    ("info", "expected"),
    [
        (membership.UserMembershipInfo(), membership.basic),
        (
            membership.UserMembershipInfo(
                member_level_by_activity=membership.pro,
                member_level_by_activity_expiration=None,
            ),
            membership.pro,
        ),
        (
            membership.UserMembershipInfo(
                patreon_email="p@example.test", sum_of_entitled_tiers_amount_cents=1500
            ),
            membership.pro,
        ),
        (membership.UserMembershipInfo(boosty_price=1500), membership.pro),
    ],
)
def test_overall_membership_uses_highest_active_source(info, expected):
    assert info.get_overall_level() == expected


def test_expired_activity_membership_does_not_raise_overall_level():
    info = membership.UserMembershipInfo(
        member_level_by_activity=membership.pro,
        member_level_by_activity_expiration=datetime.date.today()
        - datetime.timedelta(days=1),
    )
    assert info.get_overall_level() == membership.basic


@pytest.mark.parametrize(
    ("info", "expected"),
    [
        (membership.UserMembershipInfo(boosty_user_id="id"), "id"),
        (
            membership.UserMembershipInfo(boosty_user_id="id", boosty_name="Name"),
            "Name",
        ),
        (
            membership.UserMembershipInfo(
                boosty_user_id="id", boosty_email="e@example.test"
            ),
            "e@example.test",
        ),
    ],
)
def test_boosty_profile_display_prefers_email_then_name_then_id(info, expected):
    assert info.repr_boosty_profile() == expected


def test_get_membership_buttons_for_unlinked_profiles(monkeypatch):
    update = SimpleNamespace()
    monkeypatch.setattr(membership.helpers, "repr_user_from_update", lambda _: "user")
    patreon_text, patreon_button = membership.get_patreon_reply(
        update, membership.UserMembershipInfo()
    )
    boosty_text, boosty_button = membership.get_boosty_reply(
        update, membership.UserMembershipInfo()
    )

    assert patreon_text == boosty_text == ""
    assert patreon_button.callback_data == "connect_patreon"
    assert boosty_button.callback_data == "connect_boosty"


@pytest.mark.parametrize("amount", [0, 1499, 1500])
def test_linked_patreon_status_text(amount, monkeypatch):
    monkeypatch.setattr(membership.helpers, "repr_user_from_update", lambda _: "user")
    info = membership.UserMembershipInfo(
        patreon_email="p@example.test", sum_of_entitled_tiers_amount_cents=amount
    )
    text, button = membership.get_patreon_reply(SimpleNamespace(), info)
    assert "p@example.test" in text
    assert button.callback_data == "disconnect_patreon"
    assert (
        ("$14" in text)
        if amount == 1499
        else (("$15" in text) if amount == 1500 else ("не донатишь" in text))
    )


@pytest.mark.asyncio
async def test_handle_membership_basic_offers_both_links(monkeypatch):
    info = membership.UserMembershipInfo()
    monkeypatch.setattr(
        membership.helpers, "get_user", lambda _: SimpleNamespace(id=7, username="u")
    )
    monkeypatch.setattr(membership.helpers, "repr_user_from_update", lambda _: "u")
    monkeypatch.setattr(membership, "get_user_membership_info", lambda *_: info)
    bot = SimpleNamespace(send_message=AsyncMock())
    update = SimpleNamespace(effective_chat=SimpleNamespace(id=7))

    await membership.handle_membership(update, SimpleNamespace(bot=bot))

    sent = bot.send_message.await_args.kwargs
    assert "Базовый" in sent["text"]
    assert [row[0].callback_data for row in sent["reply_markup"].inline_keyboard] == [
        "connect_patreon",
        "connect_boosty",
    ]


@pytest.mark.asyncio
async def test_handle_membership_pro_uses_patreon_response(monkeypatch):
    info = membership.UserMembershipInfo(
        patreon_email="p@example.test", sum_of_entitled_tiers_amount_cents=1500
    )
    monkeypatch.setattr(
        membership.helpers, "get_user", lambda _: SimpleNamespace(id=7, username="u")
    )
    monkeypatch.setattr(membership, "get_user_membership_info", lambda *_: info)
    bot = SimpleNamespace(send_message=AsyncMock())
    update = SimpleNamespace(effective_chat=SimpleNamespace(id=7))

    await membership.handle_membership(update, SimpleNamespace(bot=bot))

    sent = bot.send_message.await_args.kwargs
    assert "Привязанный профиль Patreon" in sent["text"]
    assert (
        sent["reply_markup"].inline_keyboard[0][0].callback_data == "disconnect_patreon"
    )
