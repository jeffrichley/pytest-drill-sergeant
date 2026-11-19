"""Seeds that don't cover the draw: a seed from entropy, a seed in another test, and a
numpy seed for a stdlib draw. Analysed, never run.
"""

import random

import numpy as np
from cart import Cart

random.seed()
np.random.seed(0)


def test_seeded_itself():
    random.seed(7)
    assert Cart([random.choice(["apple"])]).total == 5


def test_sample_of_items():
    items = random.sample(["apple", "pear", "plum"], 2)  # expect: DS803
    assert len(Cart(items)) == 2


def test_seeds_only_after_drawing():
    item = random.choice(["apple", "pear"])  # expect: DS803
    random.seed(1)
    assert Cart([item]).total == 5


def test_seeds_with_none():
    random.seed(None)
    assert Cart([random.choice(["apple"])]).total == 5  # expect: DS803
