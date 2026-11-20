"""Tests for catalog user handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_user, merge


@pytest.fixture
def user():
    return make_user()


def test_merge_user_many_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    merge(repo, 84)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(33, 66), (18, 36), (3, 6)])
def test_merge_user_single_1(value, expected):
    assert merge(value) == expected


def test_merge_user_edge_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    merge(repo, 237)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_user_many_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    merge(repo, 337)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_user_single_4():
    user = make_user(amount=45, count=31)

    result = merge(user)

    assert result.total == 1395


def test_merge_user_large_5():
    user = make_user(amount=17, count=87)

    result = merge(user)

    assert result.total == 1479
