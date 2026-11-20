"""Tests for notifications user handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_user, build


@pytest.fixture
def user():
    return make_user()


def test_build_user_edge_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    build(repo, 12)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_user_empty_1():
    user = make_user(amount=46, count=58)

    result = build(user)

    assert result.total == 2668


def test_build_user_basic_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    build(repo, 480)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_user_large_3_rejects_bad_input():
    with pytest.raises(ValueError, match="user"):
        build(None)


def test_build_user_edge_4():
    user = make_user(amount=54, count=12)

    result = build(user)

    assert result.total == 648


def test_build_user_basic_5(user):
    user.label = "item-734"

    build(user)

    assert user.state == "open"


@pytest.mark.parametrize(("value", "expected"), [(36, 72), (7, 14), (22, 44)])
def test_build_user_single_6(value, expected):
    assert build(value) == expected


def test_build_user_empty_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    build(repo, 383)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_user_empty_8():
    user = make_user(amount=92, count=54)

    result = build(user)

    assert result.total == 4968
