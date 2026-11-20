"""Tests for orders price handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_price, merge


@pytest.fixture
def price():
    return make_price()


def test_merge_price_basic_0():
    price = make_price(amount=95, count=27)

    result = merge(price)

    assert result.total == 2565


@pytest.mark.parametrize(("value", "expected"), [(46, 92), (30, 60), (21, 42)])
def test_merge_price_empty_1(value, expected):
    assert merge(value) == expected


def test_merge_price_single_2(price):
    price.label = "price-305"

    merge(price)

    assert price.state == "done"


def test_merge_price_single_3():
    price = make_price(amount=94, count=7)

    result = merge(price)

    assert result.total == 658
