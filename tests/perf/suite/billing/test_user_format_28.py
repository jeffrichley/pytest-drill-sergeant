"""Tests for billing user handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_user, format


@pytest.fixture
def user():
    return make_user()


def test_format_user_large_0_rejects_bad_input():
    with pytest.raises(ValueError, match="user"):
        format(None)


def test_format_user_basic_1():
    user = make_user(amount=31, count=95)

    result = format(user)

    assert result.total == 2945


def test_format_user_edge_2(user):
    user.label = "token-869"

    format(user)

    assert user.state == "done"


def test_format_user_single_3(user):
    user.label = "item-994"

    format(user)

    assert user.state == "done"
