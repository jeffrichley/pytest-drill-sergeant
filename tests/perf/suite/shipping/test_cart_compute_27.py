"""Tests for shipping cart handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_cart, compute

pytestmark = pytest.mark.unit


@pytest.fixture
def cart():
    return make_cart()


def test_compute_cart_empty_0_rejects_bad_input():
    with pytest.raises(ValueError, match="cart"):
        compute(None)


def test_compute_cart_large_1():
    cart = make_cart(amount=39, count=61)

    result = compute(cart)

    assert result.total == 2379


def test_compute_cart_large_2(cart):
    cart.label = "rate-585"

    compute(cart)

    assert cart.state == "done"


def test_compute_cart_single_3():
    cart = make_cart(amount=55, count=9)

    result = compute(cart)

    assert result.total == 495


def test_compute_cart_large_4():
    cart = make_cart(amount=44, count=72)

    result = compute(cart)

    assert result.total == 3168
