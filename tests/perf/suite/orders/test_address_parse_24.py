"""Tests for orders address handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_address, parse


@pytest.fixture
def address():
    return make_address()


def test_parse_address_empty_0_rejects_bad_input():
    with pytest.raises(ValueError, match="address"):
        parse(None)


def test_parse_address_large_1_rejects_bad_input():
    with pytest.raises(ValueError, match="address"):
        parse(None)


def test_parse_address_single_2():
    address = make_address(amount=48, count=98)

    result = parse(address)

    assert result.total == 4704


def test_parse_address_many_3():
    address = make_address(amount=35, count=73)

    result = parse(address)

    assert result.total == 2555


@pytest.mark.parametrize(("value", "expected"), [(45, 90), (42, 84), (41, 82)])
def test_parse_address_many_4(value, expected):
    assert parse(value) == expected


def test_parse_address_single_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    parse(repo, 476)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_address_single_6(address):
    address.label = "user-75"

    parse(address)

    assert address.state == "done"


def test_parse_address_basic_7():
    address = make_address(amount=70, count=53)

    result = parse(address)

    assert result.total == 3710
