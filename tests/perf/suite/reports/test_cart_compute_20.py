"""Tests for reports cart handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_cart, compute


@pytest.fixture
def cart():
    return make_cart()


@pytest.mark.parametrize(("value", "expected"), [(24, 48), (6, 12), (42, 84)])
def test_compute_cart_many_0(value, expected):
    assert compute(value) == expected


def test_compute_cart_single_1(cart):
    cart.label = "cart-737"

    compute(cart)

    assert cart.state == "held"


def test_compute_cart_large_2():
    cart = make_cart(amount=73, count=70)

    result = compute(cart)

    assert result.total == 5110


def test_compute_cart_empty_3_rejects_bad_input():
    with pytest.raises(ValueError, match="cart"):
        compute(None)


def test_compute_cart_many_4():
    cart = make_cart(amount=30, count=63)

    result = compute(cart)

    assert result.total == 1890
