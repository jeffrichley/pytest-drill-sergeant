"""Base test classes the tests beside them inherit, composed as pandas'
`base.ExtensionTests` is. Analysed, never run."""

import pytest


class BaseAreaTests:
    def test_area_is_positive(self, shape):
        assert shape.area() > 0

    @pytest.fixture
    def test_unit(self):
        return "cm"


class BasePerimeterTests:
    def test_perimeter_is_positive(self, shape):
        assert shape.perimeter() > 0

    def test_perimeter_is_a_float(self, shape):
        assert isinstance(shape.perimeter(), float)


class ShapeTests(BaseAreaTests, BasePerimeterTests):
    pass


class FlatShapeTests(ShapeTests):
    test_area_is_positive = None
