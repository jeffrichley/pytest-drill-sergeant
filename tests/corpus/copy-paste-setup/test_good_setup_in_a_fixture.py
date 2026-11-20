"""Near-misses: the shared setup lives in a fixture, a helper that isn't a test, and
the repeated lines come after each test's first assertion, so they aren't setup.
Analysed, never run."""

import pytest
from shop import Cart, Catalog, Order


@pytest.fixture
def order():
    catalog = Catalog()
    catalog.add("apple", price=3)
    cart = Cart(catalog)
    return Order(cart)


def make_order():
    catalog = Catalog()
    catalog.add("apple", price=3)
    cart = Cart(catalog)
    return Order(cart)


def test_order_total_sums_the_lines(order):
    order.add("apple", quantity=2)
    assert order.total() == 6


def test_order_ships_once_paid(order):
    order.pay()
    assert order.status == "shipping"


def test_helper_order_starts_empty():
    first = make_order()
    assert first.total() == 0
    second = make_order()
    second.add("apple", quantity=1)
    third = make_order()
    third.add("apple", quantity=2)
    assert second.total() < third.total()


def test_helper_order_starts_unpaid():
    first = make_order()
    assert first.status == "new"
    second = make_order()
    second.add("apple", quantity=1)
    third = make_order()
    third.add("apple", quantity=2)
    assert second.status == third.status


def test_helper_order_starts_with_no_lines():
    first = make_order()
    assert first.lines == []
    second = make_order()
    second.add("apple", quantity=1)
    third = make_order()
    third.add("apple", quantity=2)
    assert len(second.lines) < len(third.lines)
