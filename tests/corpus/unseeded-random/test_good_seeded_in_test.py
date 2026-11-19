"""Near-misses: a test that seeds before it draws, and functions named like `random`'s
that aren't it, and a seed in a fixture the test asks for. Analysed, never run.
"""

import random

import pytest
from cart import Cart

from . import factories


@pytest.fixture
def seeded_random():
    random.seed(1234)


def shuffle(items):
    return sorted(items)


def test_seeds_then_draws():
    random.seed(42)
    assert Cart([random.choice(["apple"])]).total == 5


def test_local_function_named_shuffle():
    assert shuffle(["pear", "apple"]) == ["apple", "pear"]


def test_factory_draws_its_own_values():
    assert Cart([factories.item()]).total == 5


def test_draws_after_a_seeding_fixture(seeded_random):
    assert Cart([random.choice(["apple"])]).total == 5


def test_loop_variable_named_random(rngs):
    for random in rngs:  # noqa: F402 -- the shadowing is the near-miss
        assert random.choice(["apple"]) == "apple"
