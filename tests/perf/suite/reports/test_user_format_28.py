"""Tests for reports user handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_user, format

pytestmark = pytest.mark.unit


@pytest.fixture
def user():
    return make_user()


@pytest.mark.parametrize(("value", "expected"), [(17, 34), (6, 12), (33, 66)])
def test_format_user_empty_0(value, expected):
    assert format(value) == expected


def test_format_user_empty_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    format(repo, 375)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_format_user_basic_2():
    user = make_user(amount=44, count=45)

    result = format(user)

    assert result.total == 1980


def test_format_user_large_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    format(repo, 348)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_format_user_edge_4():
    user = make_user(amount=81, count=82)

    result = format(user)

    assert result.total == 6642


def test_format_user_many_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    format(repo, 336)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_format_user_empty_6():
    user = make_user(amount=70, count=15)

    result = format(user)

    assert result.total == 1050
