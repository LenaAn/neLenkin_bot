import datetime

import pytest

from membership import membership


@pytest.mark.parametrize(
    ("activity_expiration", "expected_level"),
    [
        (datetime.date.today() - datetime.timedelta(days=1), membership.basic),
        (datetime.date.today(), membership.pro),
        (datetime.date.today() + datetime.timedelta(days=1), membership.pro),
    ],
)
def test_activity_membership_pro_level_expires_after_expiry(
    activity_expiration, expected_level
):
    info = membership.UserMembershipInfo(
        member_level_by_activity=membership.pro,
        member_level_by_activity_expiration=activity_expiration,
    )

    assert info.get_activity_level() == expected_level


@pytest.mark.parametrize(
    ("patreon_email", "amount", "expected_level"),
    [
        ("member@example.com", 1499, membership.basic),
        ("member@example.com", 1500, membership.pro),
    ],
)
def test_patreon_membership_requires_link_and_minimum_amount(
    patreon_email, amount, expected_level
):
    info = membership.UserMembershipInfo(
        patreon_email=patreon_email,
        sum_of_entitled_tiers_amount_cents=amount,
    )

    assert info.get_patreon_level() == expected_level


def test_patreon_amount_without_a_linked_email_is_invalid():
    info = membership.UserMembershipInfo(sum_of_entitled_tiers_amount_cents=1500)

    with pytest.raises(Exception, match="patreon email is missing"):
        info.get_patreon_level()


@pytest.mark.parametrize(
    ("price", "expected_level"),
    [
        (1499, membership.basic),
        (1500, membership.pro),
    ],
)
def test_boosty_membership_minimum_amount(price, expected_level):
    info = membership.UserMembershipInfo(boosty_price=price)

    assert info.get_boosty_level() == expected_level
