"""Tests for search user handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_user, build

pytestmark = pytest.mark.unit


@pytest.fixture
def user():
    return make_user()


def test_build_user_large_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    build(repo, 229)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_user_basic_1(user):
    user.label = "token-738"

    build(user)

    assert user.state == "held"


def test_build_user_basic_2():
    user = make_user(amount=95, count=27)

    result = build(user)

    assert result.total == 2565


def test_build_user_edge_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    build(repo, 332)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_user_single_4(user):
    user.label = "address-500"

    build(user)

    assert user.state == "open"


def test_build_user_single_5():
    user = make_user(amount=53, count=70)

    result = build(user)

    assert result.total == 3710


def test_build_user_single_6_runs():
    build(make_user())


def test_build_user_edge_7():
    user = make_user(amount=60, count=73)

    result = build(user)

    assert result.total == 4380


def test_build_user_edge_8(user):
    user.label = "user-415"

    build(user)

    assert user.state == "done"
