"""Tests that build their inputs from the global, unseeded `random` module.

Analysed, never run.
"""

import random
from random import shuffle

from cart import Cart


def test_cart_total_for_a_random_quantity():
    quantity = random.randint(1, 10)  # expect: DS803
    assert Cart(quantity=quantity).total == quantity * 5


def test_cart_order_does_not_matter():
    items = ["apple", "pear", "plum"]
    shuffle(items)  # expect: DS803
    assert Cart(items).total == Cart(sorted(items)).total


def test_cart_with_an_unseeded_generator():
    rng = random.Random()  # expect: DS803
    item = rng.choice(["apple", "pear"])
    assert item in Cart([item])


class TestDiscounts:
    def test_random_discount_applies(self):
        rate = random.uniform(0, 0.5)  # expect: DS803
        assert Cart(["apple"], discount=rate).total <= 5
