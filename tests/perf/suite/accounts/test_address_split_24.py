"""Tests for accounts address handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_address, split

pytestmark = pytest.mark.unit


@pytest.fixture
def address():
    return make_address()


def test_split_address_single_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    split(repo, 498)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(10, 20), (1, 2), (12, 24)])
def test_split_address_single_1(value, expected):
    assert split(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(8, 16), (47, 94), (31, 62)])
def test_split_address_many_2(value, expected):
    assert split(value) == expected


def test_split_address_many_3():
    address = make_address(amount=47, count=2)

    result = split(address)

    assert result.total == 94
