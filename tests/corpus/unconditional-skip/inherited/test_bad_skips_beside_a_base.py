"""Skips on every run that inherit nothing they opt out of: a test the class
defines itself, a name the base gives only to a fixture, a base the check can't
see, a whole class, and a standalone test; and an opt-out with no reason, which
DS401 still reports. Analysed, never run."""

import unittest

import pytest
from shape_tests import ShapeTests
from shapes import Circle, Square
from third_party_shapes import ShapeContract

pytestmark = pytest.mark.unit


class TestSquare(ShapeTests):
    @pytest.fixture
    def shape(self):
        return Square(2)

    @pytest.mark.skip(reason="corners are rounded now")  # expect: DS402
    def test_square_has_four_corners(self, shape):
        assert len(shape.corners()) == 4

    def test_square_scales(self, shape):
        pytest.skip("scaling is broken")  # expect: DS402
        assert shape.scale(2).area() == 16

    @pytest.mark.skip  # expect: DS401
    def test_perimeter_is_a_float(self, shape):
        pass

    @pytest.mark.skip(reason="units moved")  # expect: DS402
    def test_unit(self, shape):
        assert shape.unit == "cm"


class TestCircle(ShapeContract):
    @pytest.mark.skip(reason="pi is approximate")  # expect: DS402
    def test_area_is_positive(self):
        assert Circle(1).area() > 0


class TestCircleCase(unittest.TestCase):
    @pytest.mark.skip(reason="radius is a property now")  # expect: DS402
    def test_radius(self):
        assert Circle(1).radius == 1


@pytest.mark.skip(reason="rewriting the circle")  # expect: DS402
class TestCircleArea(ShapeTests):
    def test_area_is_positive(self, shape):
        assert Circle(2).area() > 0


@pytest.mark.skip(reason="pre-existing failure")  # expect: DS402
def test_area_is_positive():
    assert Square(1).area() > 0
