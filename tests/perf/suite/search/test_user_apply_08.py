"""Tests for search user handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_user, apply


@pytest.fixture
def user():
    return make_user()


def test_apply_user_many_0():
    user = make_user(amount=94, count=9)

    result = apply(user)

    assert result.total == 846


def test_apply_user_empty_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    apply(repo, 111)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_user_single_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    apply(repo, 381)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_user_single_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    apply(repo, 144)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_user_empty_4():
    user = make_user(amount=41, count=49)

    result = apply(user)

    assert result.total == 2009


@pytest.mark.parametrize(("value", "expected"), [(23, 46), (34, 68), (25, 50)])
def test_apply_user_large_5(value, expected):
    assert apply(value) == expected


def test_apply_user_empty_6():
    user = make_user(amount=26, count=98)

    result = apply(user)

    assert result.total == 2548


def test_apply_user_large_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    apply(repo, 297)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_user_basic_8():
    user = make_user(amount=63, count=76)

    result = apply(user)

    assert result.total == 4788
