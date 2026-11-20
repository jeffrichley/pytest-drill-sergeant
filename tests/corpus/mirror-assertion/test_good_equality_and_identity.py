"""Near-misses: the same call on both sides that tests equality, hashing or
identity, not the code against itself. Analysed, never run."""

from dataclasses import dataclass

import pytest
from shop import get_registry

pytestmark = pytest.mark.unit


@dataclass(frozen=True)
class Point:
    x: int
    y: int


def test_points_with_the_same_coordinates_are_equal():
    assert Point(1, 2) == Point(1, 2)


def test_equal_points_hash_alike():
    assert hash(Point(1, 2)) == hash(Point(1, 2))


def test_registry_is_a_singleton():
    assert get_registry() is get_registry()
