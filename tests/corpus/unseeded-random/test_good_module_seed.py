"""Near-misses: the global generators seeded at module level, numpy imported under a
`try`. Analysed, never run.
"""

import random

import pytest
from cart import Cart

pytestmark = pytest.mark.unit

try:
    import numpy as np
except ImportError:
    np = None

random.seed(1234)
if np is not None:
    np.random.seed(1234)


def test_cart_total_for_a_seeded_quantity():
    quantity = random.randint(1, 10)
    assert Cart(quantity=quantity).total == quantity * 5


def test_numpy_draw_after_a_module_seed():
    assert np.random.rand() < 1
