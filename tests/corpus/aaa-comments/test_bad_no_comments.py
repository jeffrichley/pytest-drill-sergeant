"""Tests with no Arrange/Act/Assert comments at all, with the check enabled.
Analysed, never run."""

from shop.pricing import apply_discount


def test_add_item(cart):  # expect: DS108
    item = "apple"
    cart.add(item)
    assert cart.items == [item]


def test_total_of_an_empty_cart(cart):  # expect: DS108
    total = cart.total()
    assert total == 0


def test_discount_applies():  # expect: DS108
    assert apply_discount(price=100, rate=0.1) == 90
