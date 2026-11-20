"""Tests for catalog user handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_user, load

pytestmark = pytest.mark.unit


@pytest.fixture
def user():
    return make_user()


def test_load_user_large_0(user):
    user.label = "order-501"

    load(user)

    assert user.state == "held"


def test_load_user_basic_1(user):
    user.label = "address-283"

    load(user)

    assert user.state == "open"


@pytest.mark.parametrize(("value", "expected"), [(13, 26), (44, 88), (6, 12)])
def test_load_user_many_2(value, expected):
    assert load(value) == expected


def test_load_user_single_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    load(repo, 181)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(7, 14), (31, 62), (44, 88)])
def test_load_user_large_4(value, expected):
    assert load(value) == expected
