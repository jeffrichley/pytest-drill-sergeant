"""Near-miss: tests under different `parametrize` lists, alike but for their
values, beside a plain test of the same body. Analysed, never run."""

import pytest
from shop import Cart


@pytest.mark.parametrize("fruit", ["apple", "pear"])
def test_one_fruit_costs_three(fruit):
    cart = Cart()
    cart.add(fruit, quantity=1)
    assert cart.total() == 3


@pytest.mark.parametrize("fruit", ["plum", "fig"])
def test_one_fruit_costs_five(fruit):
    cart = Cart()
    cart.add(fruit, quantity=1)
    assert cart.total() == 5


def test_one_fruit_costs_seven(fruit):
    cart = Cart()
    cart.add(fruit, quantity=1)
    assert cart.total() == 7
