"""Near-misses: underscores that aren't private attributes: namedtuple's public
methods, keys and local names. Analysed, never run."""

import pytest
from app import Point, load

pytestmark = pytest.mark.unit


def test_namedtuple_as_dict():
    assert Point(1, 2)._asdict() == {"x": 1, "y": 2}


def test_namedtuple_replace_and_fields():
    assert Point(1, 2)._replace(x=3) == Point(3, 2)
    assert Point._fields == ("x", "y")


def test_underscore_keys():
    record = load("ada")
    assert record["_id"] == "ada"
    assert "_rev" in record


def test_underscore_local():
    _unused, value = load("pair")
    assert value == 2
