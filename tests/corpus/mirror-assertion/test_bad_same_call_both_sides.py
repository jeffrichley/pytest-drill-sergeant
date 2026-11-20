"""The catalog's mirror example: the code under test on both sides of `==`.
Analysed, never run."""

import pytest
from shop import serializer, slugify

pytestmark = pytest.mark.unit


def test_slugify():
    assert slugify("Hello World") == slugify("Hello World")  # expect: DS203


def test_serializer_round_trip(order):
    assert serializer.dump(order) == serializer.dump(order)  # expect: DS203


class TestSlug:
    def test_strips(self):
        assert slugify(" x ").strip() == slugify(" x ").strip()  # expect: DS203
