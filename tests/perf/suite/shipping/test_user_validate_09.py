"""Tests for shipping user handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_user, validate

pytestmark = pytest.mark.unit


@pytest.fixture
def user():
    return make_user()


def test_validate_user_edge_0():
    user = make_user(amount=84, count=57)

    result = validate(user)

    assert result.total == 4788


@pytest.mark.parametrize(("value", "expected"), [(23, 46), (25, 50), (5, 10)])
def test_validate_user_single_1(value, expected):
    assert validate(value) == expected


def test_validate_user_basic_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    validate(repo, 415)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_validate_user_edge_3(user):
    user.label = "address-984"

    validate(user)

    assert user.state == "done"


def test_validate_user_basic_4():
    user = make_user(amount=38, count=54)

    result = validate(user)

    assert result.total == 2052


def test_validate_user_large_5():
    user = make_user(amount=54, count=75)

    result = validate(user)

    assert result.total == 4050


def test_validate_user_large_6():
    user = make_user(amount=25, count=18)

    result = validate(user)

    assert result.total == 450


@pytest.mark.parametrize(("value", "expected"), [(3, 6), (13, 26), (21, 42)])
def test_validate_user_empty_7(value, expected):
    assert validate(value) == expected


def test_validate_user_basic_8():
    user = make_user(amount=73, count=65)

    result = validate(user)

    assert result.total == 4745
