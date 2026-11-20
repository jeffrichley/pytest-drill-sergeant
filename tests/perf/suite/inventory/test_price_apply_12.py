"""Tests for inventory price handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_price, apply


@pytest.fixture
def price():
    return make_price()


def test_apply_price_basic_0_rejects_bad_input():
    with pytest.raises(ValueError, match="price"):
        apply(None)


@pytest.mark.parametrize(("value", "expected"), [(29, 58), (5, 10), (23, 46)])
def test_apply_price_empty_1(value, expected):
    assert apply(value) == expected


def test_apply_price_large_2():
    price = make_price(amount=61, count=92)

    result = apply(price)

    assert result.total == 5612


def test_apply_price_empty_3():
    price = make_price(amount=36, count=91)

    result = apply(price)

    assert result.total == 3276


@pytest.mark.parametrize(("value", "expected"), [(18, 36), (26, 52), (44, 88)])
def test_apply_price_single_4(value, expected):
    assert apply(value) == expected
