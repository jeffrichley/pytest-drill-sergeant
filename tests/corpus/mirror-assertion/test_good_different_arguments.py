"""Near-misses: the same function on both sides, called with different
arguments, which tests a real property. Analysed, never run."""

import pytest
from shop import normalise, slugify

pytestmark = pytest.mark.unit


def test_slug_ignores_case():
    assert slugify("Hello World") == slugify("hello world")


def test_normalise_is_idempotent():
    once = normalise(" Ada ")
    assert normalise(once) == once


def test_sorted_ignores_input_order():
    assert sorted([3, 1, 2]) == sorted([2, 3, 1])
