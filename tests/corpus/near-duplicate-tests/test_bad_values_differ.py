"""The classic: three tests alike in every name, apart only in their values (one
long enough for the fix to cut it short). Analysed, never run."""

from shop import Cart


def test_one_apple_costs_three():  # expect: DS502
    cart = Cart()
    cart.add("apple", quantity=1)
    assert cart.total() == 3


def test_two_pears_cost_eight():
    cart = Cart()
    cart.add("pear", quantity=2)
    assert cart.total() == 8


def test_three_plums_cost_fifteen():
    cart = Cart()
    cart.add("plum from the orchard on the hill", quantity=3)
    assert cart.total() == 15
