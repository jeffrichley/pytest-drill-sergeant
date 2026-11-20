"""Near-miss: the setup has one shape, but each test builds it from its own values,
so no block is pasted. (Tests that differ only in values want `parametrize`, a
different finding.) Analysed, never run."""

from shop import Cart, Catalog, Order


def test_apple_order_total():
    catalog = Catalog()
    catalog.add("apple", price=3)
    cart = Cart(catalog)
    order = Order(cart)
    order.add("apple", quantity=2)
    assert order.total() == 6


def test_pear_order_total():
    catalog = Catalog()
    catalog.add("pear", price=4)
    cart = Cart(catalog)
    order = Order(cart, currency="EUR")
    order.add("pear", quantity=2)
    assert order.total() == 8


def test_plum_order_total():
    catalog = Catalog(region="us")
    catalog.add("plum", price=5)
    cart = Cart(catalog)
    order = Order(cart)
    order.add("plum", quantity=2)
    assert order.total() == 10
