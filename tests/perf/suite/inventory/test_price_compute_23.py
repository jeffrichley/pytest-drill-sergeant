"""Tests for inventory price handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_price, compute

pytestmark = pytest.mark.unit


@pytest.fixture
def price():
    return make_price()


def test_compute_price_large_0():
    price = make_price(amount=94, count=76)

    result = compute(price)

    assert result.total == 7144


def test_compute_price_basic_1():
    price = make_price(amount=87, count=65)

    result = compute(price)

    assert result.total == 5655


def test_compute_price_empty_2():
    price = make_price(amount=25, count=87)

    result = compute(price)

    assert result.total == 2175


def test_compute_price_single_3_rejects_bad_input():
    with pytest.raises(ValueError, match="price"):
        compute(None)


def test_compute_price_empty_4_works():
    result = compute(make_price())
    assert result is not None


@pytest.mark.parametrize(("value", "expected"), [(33, 66), (10, 20), (26, 52)])
def test_compute_price_basic_5(value, expected):
    assert compute(value) == expected
