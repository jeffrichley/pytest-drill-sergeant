"""Waivers that give no check code, or nothing at all."""

import pytest
from calc import add, multiply, subtract

pytestmark = pytest.mark.unit


def test_adds():  # drill: waive -- just a smoke test  # expect: DS001
    assert add(1, 2) == 3


def test_subtracts():  # drill: waive  # expect: DS001
    assert subtract(3, 1) == 2


def test_multiplies():
    result = multiply(2, 3)
    assert result  # drill: waive DS2 -- the family, not a code  # expect: DS001, DS201
