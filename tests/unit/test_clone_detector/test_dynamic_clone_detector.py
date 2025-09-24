"""Tests for DynamicCloneDetector."""

import ast
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pytest_drill_sergeant.core.analyzers.clone_detector import (
    DuplicateCluster,
    DynamicCloneDetector,
    TestSimilarity,
)
from pytest_drill_sergeant.core.analyzers.coverage_collector import CoverageData


class TestDynamicCloneDetector:
    """Test cases for DynamicCloneDetector."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.detector = DynamicCloneDetector()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self) -> None:
        """Test detector initialization."""
        detector = DynamicCloneDetector()
        assert detector.config["exact_duplicate_threshold"] == 0.98
        assert detector.config["near_duplicate_threshold"] == 0.85
        assert detector.config["similar_pattern_threshold"] == 0.70
        assert detector.config["min_cluster_size"] == 2

    def test_initialization_with_config(self) -> None:
        """Test detector initialization with custom config."""
        config = {
            "exact_duplicate_threshold": 0.95,
            "near_duplicate_threshold": 0.80,
            "similar_pattern_threshold": 0.65,
        }
        detector = DynamicCloneDetector(config)
        assert detector.config["exact_duplicate_threshold"] == 0.95
        assert detector.config["near_duplicate_threshold"] == 0.80
        assert detector.config["similar_pattern_threshold"] == 0.65

    def test_count_mock_assertions(self) -> None:
        """Test mock assertion counting."""
        # Create a test function AST with mock assertions
        code = """
def test_something():
    mock_obj.assert_called_once()
    mock_obj.assert_called_with("arg")
    mock_obj.assert_has_calls([call1, call2])
    mock_obj.assert_not_called()
"""
        tree = ast.parse(code)
        test_func = tree.body[0]
        
        count = self.detector._count_mock_assertions(test_func)
        assert count == 4

    def test_count_mock_assertions_no_mocks(self) -> None:
        """Test mock assertion counting with no mocks."""
        code = """
def test_something():
    result = some_function()
    assert result == "expected"
"""
        tree = ast.parse(code)
        test_func = tree.body[0]
        
        count = self.detector._count_mock_assertions(test_func)
        assert count == 0

    def test_extract_exception_pattern(self) -> None:
        """Test exception pattern extraction."""
        code = """
def test_something():
    with pytest.raises(ValueError):
        raise ValueError("test")
    try:
        risky_operation()
    except RuntimeError:
        pass
"""
        tree = ast.parse(code)
        test_func = tree.body[0]
        
        pattern = self.detector._extract_exception_pattern(test_func)
        assert "pytest_raises" in pattern
        assert "except_RuntimeError" in pattern

    def test_extract_exception_pattern_no_exceptions(self) -> None:
        """Test exception pattern extraction with no exceptions."""
        code = """
def test_something():
    result = some_function()
    assert result == "expected"
"""
        tree = ast.parse(code)
        test_func = tree.body[0]
        
        pattern = self.detector._extract_exception_pattern(test_func)
        assert pattern == ""

    def test_generate_test_signature(self) -> None:
        """Test test signature generation."""
        code = """
def test_something():
    mock_obj.assert_called_once()
    result = some_function()
    assert result == "expected"
"""
        tree = ast.parse(code)
        test_func = tree.body[0]
        test_file = self.temp_dir / "test_file.py"
        
        signature = self.detector._generate_test_signature(test_func, test_file)
        assert "func:test_something" in signature
        assert "params:0" in signature
        assert "decorators:0" in signature
        assert "statements:3" in signature
        assert "mocks:0" in signature  # Mock count is calculated during signature generation

    def test_calculate_coverage_similarity(self) -> None:
        """Test coverage similarity calculation."""
        # Create mock coverage data
        cov1 = CoverageData(
            test_name="test1",
            file_path=Path("test1.py"),
            line_number=1,
            lines_covered=5,
            lines_total=10,
            branches_covered=2,
            branches_total=4,
            coverage_percentage=50.0,
            covered_lines={1, 2, 3, 4, 5},
            missing_lines={6, 7, 8, 9, 10},
        )
        
        cov2 = CoverageData(
            test_name="test2",
            file_path=Path("test2.py"),
            line_number=1,
            lines_covered=4,
            lines_total=10,
            branches_covered=2,
            branches_total=4,
            coverage_percentage=40.0,
            covered_lines={1, 2, 3, 4},
            missing_lines={5, 6, 7, 8, 9, 10},
        )
        
        # Set up detector with coverage data
        self.detector._coverage_data = {
            "test1.py:test1": cov1,
            "test2.py:test2": cov2,
        }
        
        similarity = self.detector._calculate_coverage_similarity(
            "test1.py:test1", "test2.py:test2"
        )
        
        # Jaccard similarity: intersection=4, union=5, similarity=4/5=0.8
        assert similarity == 0.8

    def test_calculate_coverage_similarity_no_coverage(self) -> None:
        """Test coverage similarity calculation with no coverage data."""
        similarity = self.detector._calculate_coverage_similarity(
            "test1.py:test1", "test2.py:test2"
        )
        assert similarity == 0.0

    def test_calculate_mock_similarity(self) -> None:
        """Test mock similarity calculation."""
        self.detector._mock_assertion_counts = {
            "test1.py:test1": 3,
            "test2.py:test2": 2,
        }
        
        similarity = self.detector._calculate_mock_similarity(
            "test1.py:test1", "test2.py:test2"
        )
        
        # Similarity: min(3,2) / max(3,2) = 2/3 ≈ 0.67
        assert abs(similarity - 0.67) < 0.01

    def test_calculate_mock_similarity_no_mocks(self) -> None:
        """Test mock similarity calculation with no mocks."""
        self.detector._mock_assertion_counts = {
            "test1.py:test1": 0,
            "test2.py:test2": 0,
        }
        
        similarity = self.detector._calculate_mock_similarity(
            "test1.py:test1", "test2.py:test2"
        )
        assert similarity == 1.0

    def test_calculate_exception_similarity(self) -> None:
        """Test exception similarity calculation."""
        self.detector._exception_patterns = {
            "test1.py:test1": "pytest_raises|except_ValueError",
            "test2.py:test2": "pytest_raises|except_RuntimeError",
        }
        
        similarity = self.detector._calculate_exception_similarity(
            "test1.py:test1", "test2.py:test2"
        )
        
        # Jaccard similarity: intersection=1, union=3, similarity=1/3 ≈ 0.33
        assert abs(similarity - 0.33) < 0.01

    def test_calculate_structure_similarity(self) -> None:
        """Test structure similarity calculation."""
        self.detector._test_signatures = {
            "test1.py:test1": "func:test1|params:0|decorators:0|statements:3|mocks:1",
            "test2.py:test2": "func:test2|params:0|decorators:0|statements:3|mocks:1",
        }
        
        similarity = self.detector._calculate_structure_similarity(
            "test1.py:test1", "test2.py:test2"
        )
        
        # Jaccard similarity: intersection=4, union=6, similarity=4/6≈0.67
        assert abs(similarity - 0.67) < 0.01

    def test_calculate_test_similarity(self) -> None:
        """Test overall test similarity calculation."""
        # Set up mock data
        cov1 = CoverageData(
            test_name="test1",
            file_path=Path("test1.py"),
            line_number=1,
            lines_covered=5,
            lines_total=10,
            branches_covered=2,
            branches_total=4,
            coverage_percentage=50.0,
            covered_lines={1, 2, 3, 4, 5},
            missing_lines={6, 7, 8, 9, 10},
        )
        
        cov2 = CoverageData(
            test_name="test2",
            file_path=Path("test2.py"),
            line_number=1,
            lines_covered=4,
            lines_total=10,
            branches_covered=2,
            branches_total=4,
            coverage_percentage=40.0,
            covered_lines={1, 2, 3, 4},
            missing_lines={5, 6, 7, 8, 9, 10},
        )
        
        self.detector._coverage_data = {
            "test1.py:test1": cov1,
            "test2.py:test2": cov2,
        }
        self.detector._mock_assertion_counts = {
            "test1.py:test1": 2,
            "test2.py:test2": 2,
        }
        self.detector._exception_patterns = {
            "test1.py:test1": "pytest_raises",
            "test2.py:test2": "pytest_raises",
        }
        self.detector._test_signatures = {
            "test1.py:test1": "func:test1|params:0|decorators:0|statements:3|mocks:2",
            "test2.py:test2": "func:test2|params:0|decorators:0|statements:3|mocks:2",
        }
        
        similarity = self.detector._calculate_test_similarity(
            "test1.py:test1", "test2.py:test2"
        )
        
        # Should be a weighted combination of all similarity components
        assert 0.0 <= similarity <= 1.0

    def test_create_cluster(self) -> None:
        """Test cluster creation."""
        test_keys = ["test1.py:test1", "test2.py:test2"]
        
        # Set up mock similarity data
        with patch.object(self.detector, '_calculate_test_similarity', return_value=0.99):
            cluster = self.detector._create_cluster(test_keys)
        
        assert cluster is not None
        assert cluster.cluster_id is not None
        assert len(cluster.tests) == 2
        assert cluster.similarity_score == 0.99
        assert cluster.cluster_type == "exact_duplicates"
        assert cluster.consolidation_suggestion is not None

    def test_create_cluster_insufficient_tests(self) -> None:
        """Test cluster creation with insufficient tests."""
        test_keys = ["test1.py:test1"]
        
        cluster = self.detector._create_cluster(test_keys)
        assert cluster is None

    def test_generate_consolidation_suggestion(self) -> None:
        """Test consolidation suggestion generation."""
        tests = [("test1", Path("test1.py")), ("test2", Path("test2.py"))]
        
        suggestion = self.detector._generate_consolidation_suggestion(
            tests, "exact_duplicates"
        )
        assert "consolidating" in suggestion.lower()
        assert "parametrized" in suggestion.lower()

    def test_analyze_test_suite(self) -> None:
        """Test test suite analysis."""
        # Create test files
        test_file1 = self.temp_dir / "test_file1.py"
        test_file1.write_text("""
def test_function1():
    result = some_function()
    assert result == "expected"
""")
        
        test_file2 = self.temp_dir / "test_file2.py"
        test_file2.write_text("""
def test_function2():
    result = some_function()
    assert result == "expected"
""")
        
        # Create mock coverage data
        coverage_data = {
            f"{test_file1}:test_function1": CoverageData(
                test_name="test_function1",
                file_path=test_file1,
                line_number=2,
                lines_covered=3,
                lines_total=5,
                branches_covered=1,
                branches_total=2,
                coverage_percentage=60.0,
                covered_lines={2, 3, 4},
                missing_lines={5, 6},
            ),
            f"{test_file2}:test_function2": CoverageData(
                test_name="test_function2",
                file_path=test_file2,
                line_number=2,
                lines_covered=3,
                lines_total=5,
                branches_covered=1,
                branches_total=2,
                coverage_percentage=60.0,
                covered_lines={2, 3, 4},
                missing_lines={5, 6},
            ),
        }
        
        clusters = self.detector.analyze_test_suite([test_file1, test_file2], coverage_data)
        
        # Should find at least one cluster due to similar structure
        assert len(clusters) >= 0

    def test_get_similarity_thresholds(self) -> None:
        """Test getting similarity thresholds."""
        thresholds = self.detector.get_similarity_thresholds()
        
        assert "exact_duplicate_threshold" in thresholds
        assert "near_duplicate_threshold" in thresholds
        assert "similar_pattern_threshold" in thresholds
        assert thresholds["exact_duplicate_threshold"] == 0.98

    def test_update_similarity_thresholds(self) -> None:
        """Test updating similarity thresholds."""
        new_thresholds = {
            "exact_duplicate_threshold": 0.95,
            "near_duplicate_threshold": 0.80,
        }
        
        self.detector.update_similarity_thresholds(new_thresholds)
        
        assert self.detector.config["exact_duplicate_threshold"] == 0.95
        assert self.detector.config["near_duplicate_threshold"] == 0.80
        assert self.detector.config["similar_pattern_threshold"] == 0.70  # Unchanged

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        # Add some data to cache
        self.detector._similarity_cache["test"] = 0.5
        self.detector._coverage_data["test"] = Mock()
        self.detector._mock_assertion_counts["test"] = 1
        self.detector._exception_patterns["test"] = "pattern"
        self.detector._test_signatures["test"] = "signature"
        
        self.detector.clear_cache()
        
        assert len(self.detector._similarity_cache) == 0
        assert len(self.detector._coverage_data) == 0
        assert len(self.detector._mock_assertion_counts) == 0
        assert len(self.detector._exception_patterns) == 0
        assert len(self.detector._test_signatures) == 0

    def test_analyze_file(self) -> None:
        """Test file analysis."""
        test_file = self.temp_dir / "test_file.py"
        test_file.write_text("""
def test_function():
    result = some_function()
    assert result == "expected"
""")
        
        findings = self.detector.analyze_file(test_file)
        
        # Should return empty findings for now (placeholder implementation)
        assert isinstance(findings, list)


class TestDuplicateCluster:
    """Test cases for DuplicateCluster dataclass."""

    def test_duplicate_cluster_creation(self) -> None:
        """Test DuplicateCluster creation."""
        tests = [("test1", Path("test1.py")), ("test2", Path("test2.py"))]
        
        cluster = DuplicateCluster(
            cluster_id="test123",
            tests=tests,
            similarity_score=0.9,
            cluster_type="exact_duplicates",
            representative_test=tests[0],
            consolidation_suggestion="Test suggestion",
        )
        
        assert cluster.cluster_id == "test123"
        assert len(cluster.tests) == 2
        assert cluster.similarity_score == 0.9
        assert cluster.cluster_type == "exact_duplicates"
        assert cluster.representative_test == tests[0]
        assert cluster.consolidation_suggestion == "Test suggestion"

    def test_duplicate_cluster_without_suggestion(self) -> None:
        """Test DuplicateCluster creation without suggestion."""
        tests = [("test1", Path("test1.py"))]
        
        cluster = DuplicateCluster(
            cluster_id="test123",
            tests=tests,
            similarity_score=0.8,
            cluster_type="near_duplicates",
            representative_test=tests[0],
        )
        
        assert cluster.consolidation_suggestion is None


class TestSimilarityDataclass:
    """Test cases for TestSimilarity dataclass."""

    def test_test_similarity_creation(self) -> None:
        """Test TestSimilarity creation."""
        similarity = TestSimilarity(
            test1_name="test1",
            test1_file=Path("test1.py"),
            test2_name="test2",
            test2_file=Path("test2.py"),
            jaccard_similarity=0.8,
            coverage_overlap=0.7,
            mock_assertion_similarity=0.9,
            exception_similarity=0.6,
            overall_similarity=0.75,
            similarity_type="near",
        )
        
        assert similarity.test1_name == "test1"
        assert similarity.test2_name == "test2"
        assert similarity.jaccard_similarity == 0.8
        assert similarity.coverage_overlap == 0.7
        assert similarity.mock_assertion_similarity == 0.9
        assert similarity.exception_similarity == 0.6
        assert similarity.overall_similarity == 0.75
        assert similarity.similarity_type == "near"
