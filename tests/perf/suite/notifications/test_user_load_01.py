"""Tests for notifications user handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_user, load

pytestmark = pytest.mark.unit


@pytest.fixture
def user():
    return make_user()


def test_load_user_single_0():
    user = make_user(amount=8, count=67)

    result = load(user)

    assert result.total == 536


def test_load_user_edge_1(user):
    user.label = "invoice-549"

    load(user)

    assert user.state == "open"


@pytest.mark.parametrize(("value", "expected"), [(46, 92), (32, 64), (12, 24)])
def test_load_user_edge_2(value, expected):
    assert load(value) == expected


def test_load_user_many_3(user):
    user.label = "address-585"

    load(user)

    assert user.state == "open"


def test_load_user_basic_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    load(repo, 238)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_load_user_many_5():
    user = make_user(amount=75, count=61)

    result = load(user)

    assert result.total == 4575


def test_load_user_large_6(user):
    user.label = "token-241"

    load(user)

    assert user.state == "held"
