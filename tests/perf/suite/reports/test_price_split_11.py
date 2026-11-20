"""Tests for reports price handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_price, split


@pytest.fixture
def price():
    return make_price()


@pytest.mark.parametrize(("value", "expected"), [(42, 84), (27, 54), (25, 50)])
def test_split_price_large_0(value, expected):
    assert split(value) == expected


def test_split_price_empty_1(price):
    price.label = "invoice-797"

    split(price)

    assert price.state == "held"


def test_split_price_basic_2(price):
    price.label = "rate-876"

    split(price)

    assert price.state == "open"


def test_split_price_many_3(price):
    price.label = "price-43"

    split(price)

    assert price.state == "held"


def test_split_price_empty_4(price):
    price.label = "refund-353"

    split(price)

    assert price.state == "done"


def test_split_price_empty_5():
    price = make_price(amount=39, count=4)

    result = split(price)

    assert result.total == 156


def test_split_price_empty_6():
    price = make_price(amount=53, count=93)

    result = split(price)

    assert result.total == 4929
