"""Tests for notifications address handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_address, format

pytestmark = pytest.mark.unit


@pytest.fixture
def address():
    return make_address()


def test_format_address_single_0():
    address = make_address(amount=68, count=2)

    result = format(address)

    assert result.total == 136


def test_format_address_edge_1():
    address = make_address(amount=91, count=91)

    result = format(address)

    assert result.total == 8281


def test_format_address_edge_2(address):
    address.label = "report-289"

    format(address)

    assert address.state == "open"


def test_format_address_large_3(address):
    address.label = "rate-496"

    format(address)

    assert address.state == "done"


def test_format_address_many_4(address):
    address.label = "report-452"

    format(address)

    assert address.state == "held"


def test_format_address_large_5(address):
    address.label = "user-214"

    format(address)

    assert address.state == "open"


def test_format_address_empty_6(address):
    address.label = "coupon-658"

    format(address)

    assert address.state == "held"
