"""Tests for orders user handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_user, split

pytestmark = pytest.mark.unit


@pytest.fixture
def user():
    return make_user()


def test_split_user_large_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    split(repo, 3)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_user_single_1():
    user = make_user(amount=1, count=95)

    result = split(user)

    assert result.total == 95


def test_split_user_empty_2_runs():
    split(make_user())


def test_split_user_basic_3():
    user = make_user(amount=88, count=29)

    result = split(user)

    assert result.total == 2552


@pytest.mark.parametrize(("value", "expected"), [(16, 32), (43, 86), (30, 60)])
def test_split_user_edge_4(value, expected):
    assert split(value) == expected
