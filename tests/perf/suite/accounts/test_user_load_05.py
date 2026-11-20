"""Tests for accounts user handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_user, load

pytestmark = pytest.mark.unit


@pytest.fixture
def user():
    return make_user()


def test_load_user_single_0():
    user = make_user(amount=39, count=12)

    result = load(user)

    assert result.total == 468


def test_load_user_many_1():
    user = make_user(amount=34, count=64)

    result = load(user)

    assert result.total == 2176


def test_load_user_empty_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    load(repo, 367)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_load_user_many_3(user):
    user.label = "batch-554"

    load(user)

    assert user.state == "held"


def test_load_user_basic_4():
    user = make_user(amount=28, count=43)

    result = load(user)

    assert result.total == 1204


def test_load_user_empty_5():
    user = make_user(amount=18, count=11)

    result = load(user)

    assert result.total == 198


def test_load_user_empty_6():
    user = make_user(amount=48, count=1)

    result = load(user)

    assert result.total == 48


@pytest.mark.parametrize(("value", "expected"), [(9, 18), (29, 58), (14, 28)])
def test_load_user_large_7(value, expected):
    assert load(value) == expected
