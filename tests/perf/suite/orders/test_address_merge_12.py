"""Tests for orders address handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_address, merge

pytestmark = pytest.mark.unit


@pytest.fixture
def address():
    return make_address()


@pytest.mark.parametrize(("value", "expected"), [(48, 96), (38, 76), (44, 88)])
def test_merge_address_large_0(value, expected):
    assert merge(value) == expected


def test_merge_address_large_1(address):
    address.label = "session-461"

    merge(address)

    assert address.state == "open"


def test_merge_address_empty_2():
    address = make_address(amount=11, count=47)

    result = merge(address)

    assert result.total == 517


def test_merge_address_edge_3_rejects_bad_input():
    with pytest.raises(ValueError, match="address"):
        merge(None)


def test_merge_address_single_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    merge(repo, 314)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_address_basic_5():
    address = make_address(amount=57, count=73)

    result = merge(address)

    assert result.total == 4161


@pytest.mark.parametrize(("value", "expected"), [(20, 40), (19, 38), (16, 32)])
def test_merge_address_single_6(value, expected):
    assert merge(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(14, 28), (39, 78), (17, 34)])
def test_merge_address_many_7(value, expected):
    assert merge(value) == expected
