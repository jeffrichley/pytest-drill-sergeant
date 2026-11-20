"""Tests that draw from numpy's global or unseeded generators, with a seeding fixture
no test asks for. Analysed, never run.
"""

import numpy as np
import pytest
from numpy import random as npr
from stats import mean


@pytest.fixture
def seeded():
    np.random.seed(0)


def test_mean_of_random_samples():
    samples = np.random.rand(100)  # expect: DS803
    assert 0 <= mean(samples) <= 1


def test_mean_of_normal_samples():
    samples = npr.normal(size=100)  # expect: DS803
    assert abs(mean(samples)) < 1


def test_mean_with_an_unseeded_generator():
    rng = np.random.default_rng()  # expect: DS803
    assert 0 <= mean(rng.random(100)) <= 1
