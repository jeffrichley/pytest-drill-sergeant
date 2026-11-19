"""Near-misses: dunder attributes are Python's public protocol, not private state.
Analysed, never run."""

from app import Point, load_package


def test_point_fields():
    assert Point(1, 2).__dict__ == {"x": 1, "y": 2}


def test_class_name():
    assert type(Point(1, 2)).__name__ == "Point"
    assert Point(1, 2).__class__ is Point


def test_package_metadata():
    package = load_package("app")
    assert package.__version__
    assert "Point" in package.__all__
