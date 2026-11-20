"""Tests that read only the standard library and their own literals: Python, not
the code under test (#178). Analysed, never run."""

import math
import os
from string import ascii_lowercase

import pytest

pytestmark = pytest.mark.unit


def test_separator():  # expect: DS102
    assert os.sep == "/"


def test_pi():  # expect: DS102
    assert math.pi > 3


def test_alphabet():  # expect: DS102
    assert ascii_lowercase[0] == "a"


def test_close_enough():  # expect: DS102
    assert 0.1 + 0.2 == pytest.approx(0.3)


def test_explain_bad_example():  # expect: DS102
    discount = 0.1
    assert discount == 0.1  # expect: DS202
