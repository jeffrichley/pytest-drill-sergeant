"""Test analyzers module imports to increase coverage."""

import pytest_drill_sergeant.core.analyzers


def test_analyzers_module_imports():
    """Test importing from analyzers module to increase coverage."""
    # Test that the module has the expected attributes
    assert hasattr(pytest_drill_sergeant.core.analyzers, "__all__")
    assert hasattr(pytest_drill_sergeant.core.analyzers, "__doc__")

    # Test __all__ content
    all_items = pytest_drill_sergeant.core.analyzers.__all__
    assert isinstance(all_items, list)
    assert (
        len(all_items) == 8
    )  # This module exports AAACommentDetector, CARCalculator, CoverageCollector, CoverageSignatureGenerator, Detector, MockOverspecDetector, PrivateAccessDetector, and StructuralEqualityDetector
    assert "AAACommentDetector" in all_items
    assert "CARCalculator" in all_items
    assert "CoverageCollector" in all_items
    assert "CoverageSignatureGenerator" in all_items
    assert "Detector" in all_items
    assert "MockOverspecDetector" in all_items
    assert "PrivateAccessDetector" in all_items
    assert "StructuralEqualityDetector" in all_items

    # Test that the module is not None
    assert pytest_drill_sergeant.core.analyzers is not None

    # Test that we can access the module's file
    assert hasattr(pytest_drill_sergeant.core.analyzers, "__file__")
    assert pytest_drill_sergeant.core.analyzers.__file__ is not None


def test_analyzers_module_all():
    """Test that __all__ is properly defined."""
    __all__ = pytest_drill_sergeant.core.analyzers.__all__

    # Test that __all__ is a list
    assert isinstance(__all__, list)
    assert (
        len(__all__) == 8
    )  # This module exports AAACommentDetector, CARCalculator, CoverageCollector, CoverageSignatureGenerator, Detector, MockOverspecDetector, PrivateAccessDetector, and StructuralEqualityDetector
    assert "AAACommentDetector" in __all__
    assert "CARCalculator" in __all__
    assert "CoverageCollector" in __all__
    assert "CoverageSignatureGenerator" in __all__
    assert "Detector" in __all__
    assert "MockOverspecDetector" in __all__
    assert "PrivateAccessDetector" in __all__
    assert "StructuralEqualityDetector" in __all__
