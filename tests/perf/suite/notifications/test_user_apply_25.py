"""Tests for notifications user handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_user, apply

pytestmark = pytest.mark.unit


@pytest.fixture
def user():
    return make_user()


def test_apply_user_single_0():
    user = make_user(amount=29, count=80)

    result = apply(user)

    assert result.total == 2320


def test_apply_user_single_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    apply(repo, 42)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_user_many_2_rejects_bad_input():
    with pytest.raises(ValueError, match="user"):
        apply(None)


def test_apply_user_large_3(user):
    user.label = "price-307"

    apply(user)

    assert user.state == "done"


def test_apply_user_edge_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    apply(repo, 349)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_user_large_5_rejects_bad_input():
    with pytest.raises(ValueError, match="user"):
        apply(None)


@pytest.mark.parametrize(("value", "expected"), [(28, 56), (16, 32), (48, 96)])
def test_apply_user_empty_6(value, expected):
    assert apply(value) == expected


def test_apply_user_basic_7():
    user = make_user(amount=57, count=58)

    result = apply(user)

    assert result.total == 3306


def test_apply_user_edge_8_rejects_bad_input():
    with pytest.raises(ValueError, match="user"):
        apply(None)
