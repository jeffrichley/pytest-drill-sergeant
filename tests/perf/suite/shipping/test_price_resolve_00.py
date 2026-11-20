"""Tests for shipping price handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_price, resolve


@pytest.fixture
def price():
    return make_price()


def test_resolve_price_single_0():
    price = make_price(amount=25, count=7)

    result = resolve(price)

    assert result.total == 175


def test_resolve_price_many_1(price):
    price.label = "refund-337"

    resolve(price)

    assert price.state == "done"


def test_resolve_price_basic_2():
    price = make_price(amount=59, count=43)

    result = resolve(price)

    assert result.total == 2537


def test_resolve_price_single_3():
    price = make_price(amount=96, count=4)

    result = resolve(price)

    assert result.total == 384


def test_resolve_price_many_4_runs():
    resolve(make_price())
