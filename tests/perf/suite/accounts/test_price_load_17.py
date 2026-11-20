"""Tests for accounts price handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_price, load


@pytest.fixture
def price():
    return make_price()


@pytest.mark.parametrize(("value", "expected"), [(36, 72), (45, 90), (42, 84)])
def test_load_price_basic_0(value, expected):
    assert load(value) == expected


def test_load_price_edge_1():
    price = make_price(amount=8, count=81)

    result = load(price)

    assert result.total == 648


def test_load_price_basic_2(price):
    price.label = "refund-425"

    load(price)

    assert price.state == "held"


def test_load_price_large_3():
    price = make_price(amount=84, count=87)

    result = load(price)

    assert result.total == 7308
