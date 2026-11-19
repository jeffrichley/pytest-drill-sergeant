"""Near-miss: an autouse fixture seeds the global generator before every test.

Analysed, never run.
"""

import random

import pytest
from cart import Cart


@pytest.fixture(autouse=True)
def _seed_random():
    random.seed(1234)


def test_cart_total_for_a_seeded_quantity():
    quantity = random.randint(1, 10)
    assert Cart(quantity=quantity).total == quantity * 5
