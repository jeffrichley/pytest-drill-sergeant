"""Tests for catalog user handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_user, load

pytestmark = pytest.mark.unit


@pytest.fixture
def user():
    return make_user()


def test_load_user_empty_0(user):
    user.label = "report-94"

    load(user)

    assert user.state == "held"


@pytest.mark.parametrize(("value", "expected"), [(45, 90), (21, 42), (26, 52)])
def test_load_user_edge_1(value, expected):
    assert load(value) == expected


def test_load_user_large_2():
    user = make_user(amount=81, count=31)

    result = load(user)

    assert result.total == 2511


def test_load_user_basic_3():
    user = make_user(amount=50, count=79)

    result = load(user)

    assert result.total == 3950


def test_load_user_many_4():
    user = make_user(amount=84, count=65)

    result = load(user)

    assert result.total == 5460


def test_load_user_single_5():
    user = make_user(amount=97, count=35)

    result = load(user)

    assert result.total == 3395


def test_load_user_single_6():
    user = make_user(amount=33, count=52)

    result = load(user)

    assert result.total == 1716
