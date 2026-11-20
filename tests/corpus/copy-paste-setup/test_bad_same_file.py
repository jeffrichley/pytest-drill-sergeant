"""The headline: one setup block pasted into three tests of one file. Analysed,
never run."""

import pytest
from shop import Cart, Catalog, Order

pytestmark = pytest.mark.unit


def test_order_total_sums_the_lines():
    catalog = Catalog()  # expect: DS501
    catalog.add("apple", price=3)
    cart = Cart(catalog)
    order = Order(cart)
    order.add("apple", quantity=2)
    assert order.total() == 6


def test_order_ships_once_paid():
    catalog = Catalog()
    catalog.add("apple", price=3)
    cart = Cart(catalog)
    order = Order(cart)
    order.pay()
    assert order.status == "shipping"


def test_order_cancel_empties_the_cart():
    catalog = Catalog()
    catalog.add("apple", price=3)
    cart = Cart(catalog)
    order = Order(cart)
    order.cancel()
    assert cart.lines == []
