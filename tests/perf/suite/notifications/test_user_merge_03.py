"""Tests for notifications user handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_user, merge

pytestmark = pytest.mark.unit


@pytest.fixture
def user():
    return make_user()


@pytest.mark.parametrize(("value", "expected"), [(42, 84), (19, 38), (1, 2)])
def test_merge_user_single_0(value, expected):
    assert merge(value) == expected


def test_merge_user_large_1():
    user = make_user(amount=21, count=78)

    result = merge(user)

    assert result.total == 1638


def test_merge_user_single_2():
    user = make_user(amount=96, count=8)

    result = merge(user)

    assert result.total == 768


def test_merge_user_single_3():
    user = make_user(amount=91, count=35)

    result = merge(user)

    assert result.total == 3185


def test_merge_user_many_4_rejects_bad_input():
    with pytest.raises(ValueError, match="user"):
        merge(None)


def test_merge_user_empty_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    merge(repo, 222)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(16, 32), (6, 12), (7, 14)])
def test_merge_user_many_6(value, expected):
    assert merge(value) == expected
