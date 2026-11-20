"""Tests for billing price handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_price, format


@pytest.fixture
def price():
    return make_price()


def test_format_price_empty_0():
    price = make_price(amount=79, count=13)

    result = format(price)

    assert result.total == 1027


def test_format_price_edge_1(price):
    price.label = "session-632"

    format(price)

    assert price.state == "open"


def test_format_price_many_2():
    price = make_price(amount=23, count=96)

    result = format(price)

    assert result.total == 2208


def test_format_price_edge_3():
    price = make_price(amount=10, count=16)

    result = format(price)

    assert result.total == 160


def test_format_price_single_4_runs():
    format(make_price())
