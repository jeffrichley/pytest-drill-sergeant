"""Near-miss, with its neighbour: a test alike but for its values to one in another
file, which one parametrized function can't hold. Analysed, never run."""

import pytest
from shop import Cart

pytestmark = pytest.mark.unit


def test_two_pears_cost_eight():
    cart = Cart()
    cart.add("pear", quantity=2)
    assert cart.total() == 8
