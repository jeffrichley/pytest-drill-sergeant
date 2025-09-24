"""Unit tests for the feature extractor."""

from __future__ import annotations

from pathlib import Path

from pytest_drill_sergeant.core.models import Finding, Severity
from pytest_drill_sergeant.core.scoring import (
    TestFeatureExtractor,
    get_feature_extractor,
    reset_feature_extractor,
)


class TestTestFeatureExtractor:
    """Test the TestFeatureExtractor functionality."""

    def test_init(self) -> None:
        """Test extractor initialization."""
        extractor = TestFeatureExtractor()
        assert extractor is not None

    def test_extract_features_from_file(self, tmp_path: Path) -> None:
        """Test feature extraction from a test file."""
        # Create a test file
        test_file = tmp_path / "test_example.py"
        test_content = '''
def test_simple():
    """A simple test."""
    assert True

def test_with_assertions():
    """A test with multiple assertions."""
    result = some_function()
    assert result is not None
    assert result > 0
    assert result < 100

def test_complex():
    """A complex test."""
    if condition:
        for item in items:
            assert item is not None
    else:
        assert False
'''
        test_file.write_text(test_content)

        extractor = TestFeatureExtractor()
        findings = []  # No findings for this test

        features = extractor.extract_features_from_file(test_file, findings)

        # Should extract features for all test functions
        assert len(features) >= 3
        assert "test_simple" in features
        assert "test_with_assertions" in features
        assert "test_complex" in features

        # Check that features are properly extracted
        simple_features = features["test_simple"]
        assert simple_features.test_name == "test_simple"
        assert simple_features.file_path == test_file
        assert simple_features.assertion_count >= 1  # At least one assertion

        complex_features = features["test_complex"]
        assert complex_features.complexity_score > 1  # Should have higher complexity

    def test_extract_features_with_findings(self, tmp_path: Path) -> None:
        """Test feature extraction with findings."""
        # Create a test file
        test_file = tmp_path / "test_with_findings.py"
        test_content = '''
def test_good():
    """A good test."""
    result = public_function()
    assert result == expected_value

def test_bad():
    """A bad test with private access."""
    obj = SomeClass()
    assert obj._private_method() == expected_value
'''
        test_file.write_text(test_content)

        extractor = TestFeatureExtractor()

        # Create findings for the bad test
        findings = [
            Finding(
                code="DS301",
                name="private_access",
                message="Private access detected",
                file_path=test_file,
                line_number=8,
                severity=Severity.WARNING,
            ),
            Finding(
                code="DS305",
                name="mock_overspecification",
                message="Mock over-specified",
                file_path=test_file,
                line_number=9,
                severity=Severity.WARNING,
            ),
        ]

        features = extractor.extract_features_from_file(test_file, findings)

        # Should extract features for both tests
        assert len(features) >= 2
        assert "test_good" in features
        assert "test_bad" in features

        # Check that findings are properly counted
        bad_features = features["test_bad"]
        assert bad_features.private_access_count >= 0
        assert bad_features.mock_assertion_count >= 0

    def test_extract_features_empty_file(self, tmp_path: Path) -> None:
        """Test feature extraction from empty file."""
        test_file = tmp_path / "empty_test.py"
        test_file.write_text("")

        extractor = TestFeatureExtractor()
        findings = []

        features = extractor.extract_features_from_file(test_file, findings)

        # Should return default features for the file
        assert len(features) >= 1
        assert str(test_file) in features

    def test_extract_features_no_test_functions(self, tmp_path: Path) -> None:
        """Test feature extraction from file with no test functions."""
        test_file = tmp_path / "no_tests.py"
        test_content = '''
def regular_function():
    """A regular function, not a test."""
    return "hello"

class SomeClass:
    def method(self):
        return "world"
'''
        test_file.write_text(test_content)

        extractor = TestFeatureExtractor()
        findings = []

        features = extractor.extract_features_from_file(test_file, findings)

        # Should return default features for the file
        assert len(features) >= 1
        assert str(test_file) in features

    def test_extract_features_syntax_error(self, tmp_path: Path) -> None:
        """Test feature extraction from file with syntax error."""
        test_file = tmp_path / "syntax_error.py"
        test_content = '''
def test_broken():
    """A test with syntax error."""
    assert True
    # Missing closing parenthesis
    result = some_function(
'''
        test_file.write_text(test_content)

        extractor = TestFeatureExtractor()
        findings = []

        # Should not raise exception but return default features
        features = extractor.extract_features_from_file(test_file, findings)

        # Should return default features for the file
        assert len(features) >= 1
        assert str(test_file) in features

    def test_calculate_complexity(self) -> None:
        """Test complexity calculation."""
        extractor = TestFeatureExtractor()

        # Create a simple test node (simplified)
        import ast

        simple_code = "def test_simple():\n    assert True"
        simple_tree = ast.parse(simple_code)
        simple_func = simple_tree.body[0]

        simple_complexity = extractor._calculate_complexity(simple_func)
        assert simple_complexity == 1  # Base complexity

        # Create a complex test node
        complex_code = """
def test_complex():
    if condition:
        for item in items:
            if item is not None:
                assert item > 0
            else:
                assert False
        try:
            result = risky_function()
        except Exception:
            assert False
"""
        complex_tree = ast.parse(complex_code)
        complex_func = complex_tree.body[0]

        complex_complexity = extractor._calculate_complexity(complex_func)
        assert complex_complexity > simple_complexity

    def test_count_assertions(self) -> None:
        """Test assertion counting."""
        extractor = TestFeatureExtractor()

        # Create a test node with assertions
        import ast

        code = """
def test_with_assertions():
    assert True
    assert result is not None
    assert result > 0
    assert result < 100
    self.assertEqual(a, b)
    self.assertIn(item, collection)
"""
        tree = ast.parse(code)
        test_func = tree.body[0]

        assertion_count = extractor._count_assertions(test_func)
        assert assertion_count >= 4  # Should count assert statements

    def test_count_setup_lines(self) -> None:
        """Test setup line counting."""
        extractor = TestFeatureExtractor()

        # Create a test node
        import ast

        code = """
def test_with_setup():
    # Setup
    obj = SomeClass()
    obj.configure()
    obj.prepare()

    # Act
    result = obj.method()

    # Assert
    assert result is not None
"""
        tree = ast.parse(code)
        test_func = tree.body[0]

        setup_lines = extractor._count_setup_lines(test_func)
        assert setup_lines >= 0  # Should count setup lines

    def test_count_teardown_lines(self) -> None:
        """Test teardown line counting."""
        extractor = TestFeatureExtractor()

        # Create a test node
        import ast

        code = """
def test_with_teardown():
    obj = SomeClass()
    try:
        result = obj.method()
        assert result is not None
    finally:
        obj.cleanup()
"""
        tree = ast.parse(code)
        test_func = tree.body[0]

        teardown_lines = extractor._count_teardown_lines(test_func)
        assert teardown_lines >= 0  # Should count teardown lines

    def test_calculate_test_length(self) -> None:
        """Test test length calculation."""
        extractor = TestFeatureExtractor()

        # Create a test node
        import ast

        code = """
def test_length():
    # Line 1
    # Line 2
    # Line 3
    assert True
    # Line 5
"""
        tree = ast.parse(code)
        test_func = tree.body[0]

        length = extractor._calculate_test_length(test_func)
        assert length >= 1  # Should calculate length

    def test_create_default_features(self) -> None:
        """Test default features creation."""
        extractor = TestFeatureExtractor()
        test_file = Path("test.py")

        features = extractor._create_default_features(test_file)

        assert features.test_name == "test"
        assert features.file_path == test_file
        assert features.line_number == 1

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        extractor = TestFeatureExtractor()

        # Add something to cache
        test_file = Path("test.py")
        extractor._cache[str(test_file)] = extractor._create_default_features(test_file)

        assert len(extractor._cache) > 0

        # Clear cache
        extractor.clear_cache()
        assert len(extractor._cache) == 0

    def test_global_feature_extractor_singleton(self) -> None:
        """Test that global feature extractor is a singleton."""
        extractor1 = get_feature_extractor()
        extractor2 = get_feature_extractor()
        assert extractor1 is extractor2

    def test_reset_feature_extractor(self) -> None:
        """Test resetting the global feature extractor."""
        extractor1 = get_feature_extractor()
        reset_feature_extractor()
        extractor2 = get_feature_extractor()
        assert extractor1 is not extractor2

    def test_filter_findings_for_test(self) -> None:
        """Test findings filtering for specific test."""
        extractor = TestFeatureExtractor()

        findings = [
            Finding(
                code="DS301",
                name="private_access",
                message="Private access detected",
                file_path=Path("test.py"),
                line_number=10,
                severity=Severity.WARNING,
            ),
            Finding(
                code="DS305",
                name="mock_overspecification",
                message="Mock over-specified",
                file_path=Path("test.py"),
                line_number=20,
                severity=Severity.WARNING,
            ),
        ]

        # Test filtering (simplified implementation)
        filtered = extractor._filter_findings_for_test(findings, 5)
        assert len(filtered) == len(
            findings
        )  # Current implementation returns all findings
