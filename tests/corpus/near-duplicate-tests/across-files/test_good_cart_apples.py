"""Near-miss, with its neighbour: a test alike but for its values to one in another
file, which one parametrized function can't hold. Analysed, never run."""

import pytest
from shop import Cart

pytestmark = pytest.mark.unit


def test_one_apple_costs_three():
    cart = Cart()
    cart.add("apple", quantity=1)
    assert cart.total() == 3
