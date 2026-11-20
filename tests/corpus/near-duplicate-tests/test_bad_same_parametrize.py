"""Tests under the very same `parametrize`, apart only in a value of their bodies:
a second `parametrize` holds them both. Analysed, never run."""

import pytest
from shop import Cart

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("fruit", ["apple", "pear"])
def test_one_fruit_costs_three(fruit):  # expect: DS502
    cart = Cart()
    cart.add(fruit, quantity=1)
    assert cart.total() == 3


@pytest.mark.parametrize("fruit", ["apple", "pear"])
def test_two_fruits_cost_six(fruit):
    cart = Cart()
    cart.add(fruit, quantity=2)
    assert cart.total() == 6
