"""The golden suite's cart tests. Analysed by the golden test, never run."""

import pytest

from shop.cart import Cart

pytestmark = pytest.mark.unit


def test_adding_an_item_to_the_cart():
    cart = Cart()
    cart.add("apple", quantity=3)


def test_cart_total_sums_its_lines():
    cart = Cart()
    cart.add("apple", quantity=2, price=50)
    cart.add("pear", quantity=1, price=75)

    assert cart.total() == 175


def test_empty_cart_smoke():  # drill: waive DS101 -- import smoke test for the release
    Cart()
