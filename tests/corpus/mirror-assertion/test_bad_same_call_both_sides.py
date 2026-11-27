"""The catalog's mirror example: the code under test on both sides of `==`.
Analysed, never run."""

import pytest
import serializer
from shop import slugify

pytestmark = pytest.mark.unit


def test_slugify():
    assert slugify("Hello World") == slugify("Hello World")  # expect: DS203


def test_serializer_round_trip(order):
    assert serializer.dump(order) == serializer.dump(order)  # expect: DS203


class TestSlug:
    def test_strips(self):
        assert slugify(" x ").strip() == slugify(" x ").strip()  # expect: DS203


def test_slug_wrapped_in_a_builtin_type():
    assert list(slugify("a b")) == list(slugify("a b"))  # expect: DS203


def test_local_name_shadowing_a_builtin():
    str = slugify  # noqa: A001
    assert str("a b") == str("a b")  # expect: DS203
