"""Two tests alike in every name and literal too: a copy under a second name, and
a pair of tests apart only in a negative number. Analysed, never run."""

from shop import Cart


def test_empty_cart_totals_zero():  # expect: DS502
    cart = Cart()
    assert cart.total() == 0


def test_new_cart_has_no_total():
    cart = Cart()
    assert cart.total() == 0


def test_refund_of_one_lowers_the_balance():  # expect: DS502
    cart = Cart()
    cart.refund(-1)
    assert cart.balance() == -1


def test_refund_of_five_lowers_the_balance():
    cart = Cart()
    cart.refund(-5)
    assert cart.balance() == -5
