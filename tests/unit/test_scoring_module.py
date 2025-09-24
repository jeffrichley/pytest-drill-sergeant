"""Test scoring module imports to increase coverage."""

import pytest_drill_sergeant.core.scoring


def test_scoring_module_imports():
    """Test importing from scoring module to increase coverage."""
    # Test that the module has the expected attributes
    assert hasattr(pytest_drill_sergeant.core.scoring, "__all__")
    assert hasattr(pytest_drill_sergeant.core.scoring, "__doc__")

    # Test __all__ content
    all_items = pytest_drill_sergeant.core.scoring.__all__
    assert isinstance(all_items, list)
    assert len(all_items) == 10  # This module exports 10 items (added BIS components)
    assert "BRSCalculator" in all_items
    assert "RunMetrics" in all_items
    assert "DynamicBISCalculator" in all_items
    assert "BISMetrics" in all_items
    assert "BISCalculator" in all_items
    assert "FeatureExtractor" in all_items
    assert "get_bis_calculator" in all_items
    assert "reset_bis_calculator" in all_items
    assert "get_feature_extractor" in all_items
    assert "reset_feature_extractor" in all_items

    # Test that the module is not None
    assert pytest_drill_sergeant.core.scoring is not None

    # Test that we can access the module's file
    assert hasattr(pytest_drill_sergeant.core.scoring, "__file__")
    assert pytest_drill_sergeant.core.scoring.__file__ is not None


def test_scoring_module_all():
    """Test that __all__ is properly defined."""
    __all__ = pytest_drill_sergeant.core.scoring.__all__

    # Test that __all__ is a list
    assert isinstance(__all__, list)
    assert len(__all__) == 10  # This module exports 10 items (added BIS components)

    # Test that all expected items are present
    expected_items = [
        "BRSCalculator",
        "RunMetrics",
        "DynamicBISCalculator",
        "BISMetrics",
        "BISCalculator",
        "FeatureExtractor",
        "get_bis_calculator",
        "reset_bis_calculator",
        "get_feature_extractor",
        "reset_feature_extractor",
    ]
    for item in expected_items:
        assert item in __all__
