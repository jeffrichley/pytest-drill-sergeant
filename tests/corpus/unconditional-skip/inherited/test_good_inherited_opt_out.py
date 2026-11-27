"""Near-misses: a subclass opting out of a test it inherits from a base class in
the test tree, modelled on pandas' `tests/extension/test_datetime.py` and
`test_numpy.py`, the base imported or a class beside it in the class around.
The base's test still runs for every other subclass. Analysed, never run."""

import pytest
import shape_tests
from shape_tests import ShapeTests
from shapes import Line, Point

pytestmark = pytest.mark.unit


class TestLine(ShapeTests):
    @pytest.fixture
    def shape(self):
        return Line(3)

    @pytest.mark.skip(reason="a line has no area")
    def test_area_is_positive(self, shape):
        pass

    def test_perimeter_is_a_float(self, shape):
        pytest.skip("a line's length is an int")


class TestPoint(shape_tests.ShapeTests):
    @pytest.fixture
    def shape(self):
        return Point()

    @pytest.mark.skip(reason="a point has no perimeter")
    def test_perimeter_is_positive(self, shape):
        pass


class TestPolygons:
    class SideTests:
        def test_has_sides(self, shape):
            assert shape.sides() > 0

    class TestHexagon(SideTests):
        @pytest.mark.skip(reason="sides are counted per edge")
        def test_has_sides(self, shape):
            pass
