"""Near-misses: generators built with a seed, and draws from a generator fixture.

Analysed, never run.
"""

import random

import numpy as np
import pytest
from cart import Cart

pytestmark = pytest.mark.unit

SEED = 1234


def test_cart_with_a_seeded_generator():
    rng = random.Random(SEED)
    quantity = rng.randint(1, 10)
    assert Cart(quantity=quantity).total == quantity * 5


def test_mean_with_a_seeded_numpy_generator():
    rng = np.random.default_rng(0)
    assert rng.random(3).shape == (3,)


def test_legacy_numpy_state_with_a_seed():
    state = np.random.RandomState(seed=1)
    assert state.randint(10) < 10


def test_draws_from_a_generator_fixture(rng):
    assert Cart([rng.choice(["apple"])]).total == 5
