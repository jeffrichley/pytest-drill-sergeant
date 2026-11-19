"""Near-misses: a test that seeds before it draws, and functions named like `random`'s
that aren't it. Analysed, never run.
"""

import random

from cart import Cart

from . import factories


def shuffle(items):
    return sorted(items)


def test_seeds_then_draws():
    random.seed(42)
    assert Cart([random.choice(["apple"])]).total == 5


def test_local_function_named_shuffle():
    assert shuffle(["pear", "apple"]) == ["apple", "pear"]


def test_factory_draws_its_own_values():
    assert Cart([factories.item()]).total == 5
