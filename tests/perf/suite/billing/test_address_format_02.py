"""Tests for billing address handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_address, format


@pytest.fixture
def address():
    return make_address()


def test_format_address_empty_0(address):
    address.label = "address-449"

    format(address)

    assert address.state == "open"


@pytest.mark.parametrize(("value", "expected"), [(3, 6), (34, 68), (33, 66)])
def test_format_address_single_1(value, expected):
    assert format(value) == expected


def test_format_address_edge_2(address):
    address.label = "cart-732"

    format(address)

    assert address.state == "open"


def test_format_address_empty_3():
    address = make_address(amount=37, count=22)

    result = format(address)

    assert result.total == 814


@pytest.mark.parametrize(("value", "expected"), [(48, 96), (10, 20), (9, 18)])
def test_format_address_basic_4(value, expected):
    assert format(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(31, 62), (38, 76), (32, 64)])
def test_format_address_large_5(value, expected):
    assert format(value) == expected
