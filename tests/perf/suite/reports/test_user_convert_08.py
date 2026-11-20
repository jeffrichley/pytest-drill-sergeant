"""Tests for reports user handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_user, convert

pytestmark = pytest.mark.unit


@pytest.fixture
def user():
    return make_user()


@pytest.mark.parametrize(("value", "expected"), [(41, 82), (22, 44), (9, 18)])
def test_convert_user_basic_0(value, expected):
    assert convert(value) == expected


def test_convert_user_empty_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    convert(repo, 75)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_user_basic_2():
    user = make_user(amount=47, count=51)

    result = convert(user)

    assert result.total == 2397


def test_convert_user_empty_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    convert(repo, 90)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(47, 94), (42, 84), (49, 98)])
def test_convert_user_empty_4(value, expected):
    assert convert(value) == expected
