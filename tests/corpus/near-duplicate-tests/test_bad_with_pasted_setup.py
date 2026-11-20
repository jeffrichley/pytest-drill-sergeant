"""Near-duplicates that also share a setup block pasted into three tests: one
finding, for parametrize, which takes the pasted setup with it; no copy-paste-setup
finding. Analysed, never run."""

from shop import Cart, Catalog, Order


def test_order_of_one_apple():  # expect: DS502
    catalog = Catalog()
    catalog.add("apple", price=4)
    cart = Cart(catalog)
    order = Order(cart)
    order.add("apple", quantity=1)
    assert order.total() == 4


def test_order_of_two_apples():
    catalog = Catalog()
    catalog.add("apple", price=4)
    cart = Cart(catalog)
    order = Order(cart)
    order.add("apple", quantity=2)
    assert order.total() == 8


def test_order_of_three_apples():
    catalog = Catalog()
    catalog.add("apple", price=4)
    cart = Cart(catalog)
    order = Order(cart)
    order.add("apple", quantity=3)
    assert order.total() == 12
