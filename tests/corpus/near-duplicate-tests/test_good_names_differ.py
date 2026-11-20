"""Near-miss: tests of one shape that differ in a name (the function they call,
the class they build) or an attribute, not only in their values. Analysed, never
run."""

from shop import Cart, Wishlist, parse_price, parse_quantity


def test_parse_price():
    assert parse_price("3") == 3


def test_parse_quantity():
    assert parse_quantity("3") == 3


def test_cart_starts_empty():
    basket = Cart()
    assert basket.size() == 0


def test_wishlist_starts_empty():
    basket = Wishlist()
    assert basket.size() == 0


def test_cart_total_of_one_apple():
    cart = Cart(["apple"])
    assert cart.total == 3


def test_cart_weight_of_one_apple():
    cart = Cart(["apple"])
    assert cart.weight == 3
