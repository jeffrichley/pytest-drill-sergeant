"""Tests for coverage integration functionality."""

from pathlib import Path
from unittest.mock import patch

from pytest_drill_sergeant.core.analyzers.car_calculator import CARCalculator, CARResult
from pytest_drill_sergeant.core.analyzers.coverage_collector import (
    CoverageCollector,
    CoverageData,
)
from pytest_drill_sergeant.core.analyzers.coverage_signature import (
    CoverageSignature,
    CoverageSignatureGenerator,
)


class TestCoverageCollector:
    """Test coverage collector functionality."""

    def test_coverage_collector_initialization(self):
        """Test coverage collector initialization."""
        collector = CoverageCollector()
        assert collector._coverage_data == {}
        assert collector._temp_dir is None

    def test_start_coverage(self):
        """Test starting coverage collection."""
        collector = CoverageCollector()
        collector.start_coverage()
        
        assert collector._temp_dir is not None
        assert collector._temp_dir.exists()
        assert hasattr(collector, "cov")
        
        collector.stop_coverage()

    def test_stop_coverage(self):
        """Test stopping coverage collection."""
        collector = CoverageCollector()
        collector.start_coverage()
        collector.stop_coverage()
        
        assert collector._temp_dir is None

    def test_find_source_files(self):
        """Test finding source files."""
        collector = CoverageCollector()
        
        # Create a mock test file path
        test_file_path = Path("/tmp/test_example.py")
        
        # Mock the parent directory structure
        with patch.object(Path, "exists", return_value=False), \
             patch.object(Path, "rglob", return_value=[]), \
             patch.object(Path, "iterdir", return_value=[]):
            
            source_files = collector._find_source_files(test_file_path)
            assert isinstance(source_files, list)

    def test_is_test_file(self):
        """Test test file detection."""
        collector = CoverageCollector()
        
        # Test files
        assert collector._is_test_file(Path("test_example.py"))
        assert collector._is_test_file(Path("example_test.py"))
        assert collector._is_test_file(Path("test/example.py"))
        
        # Non-test files
        assert not collector._is_test_file(Path("example.py"))
        assert not collector._is_test_file(Path("src/example.py"))

    def test_analyze_file(self):
        """Test file analysis."""
        collector = CoverageCollector()
        
        # Test with non-existent file
        findings = collector.analyze_file(Path("/nonexistent.py"))
        assert findings == []


class TestCARCalculator:
    """Test CAR calculator functionality."""

    def test_car_calculator_initialization(self):
        """Test CAR calculator initialization."""
        calculator = CARCalculator()
        assert calculator.logger.name == "drill_sergeant.car_calculator"

    def test_calculate_car_score(self):
        """Test CAR score calculation."""
        calculator = CARCalculator()
        
        # Test with assertions (80 / 5) * 100 = 1600, capped at 100
        score = calculator._calculate_car_score(5, 80.0)
        assert score == 100.0  # Capped at 100
        
        # Test with no assertions
        score = calculator._calculate_car_score(0, 80.0)
        assert score == 0.0
        
        # Test with high score (should be capped at 100)
        score = calculator._calculate_car_score(1, 150.0)
        assert score == 100.0

    def test_determine_car_grade(self):
        """Test CAR grade determination."""
        calculator = CARCalculator()
        
        assert calculator._determine_car_grade(95.0) == "A"
        assert calculator._determine_car_grade(85.0) == "B"
        assert calculator._determine_car_grade(75.0) == "C"
        assert calculator._determine_car_grade(65.0) == "D"
        assert calculator._determine_car_grade(55.0) == "F"

    def test_determine_efficiency_level(self):
        """Test efficiency level determination."""
        calculator = CARCalculator()
        
        assert calculator._determine_efficiency_level(85.0, 5, 85.0) == "highly_efficient"
        assert calculator._determine_efficiency_level(65.0, 5, 65.0) == "efficient"
        assert calculator._determine_efficiency_level(45.0, 5, 45.0) == "moderately_efficient"
        assert calculator._determine_efficiency_level(30.0, 0, 30.0) == "no_assertions"
        assert calculator._determine_efficiency_level(30.0, 5, 15.0) == "low_coverage"
        assert calculator._determine_efficiency_level(30.0, 5, 30.0) == "inefficient"

    def test_calculate_car(self):
        """Test complete CAR calculation."""
        calculator = CARCalculator()
        
        # Create mock coverage data
        coverage_data = CoverageData(
            test_name="test_example",
            file_path=Path("/tmp/test_example.py"),
            line_number=10,
            lines_covered=80,
            lines_total=100,
            branches_covered=40,
            branches_total=50,
            coverage_percentage=80.0,
            covered_lines={1, 2, 3, 4, 5},
            missing_lines={6, 7, 8, 9, 10},
        )
        
        # Mock the assertion counting
        with patch.object(calculator, "_count_assertions", return_value=5):
            result = calculator.calculate_car(
                Path("/tmp/test_example.py"), "test_example", 10, coverage_data
            )
            
            assert isinstance(result, CARResult)
            assert result.test_name == "test_example"
            assert result.assertion_count == 5
            assert result.coverage_percentage == 80.0
            assert result.car_score == 100.0  # Capped at 100
            assert result.car_grade == "A"
            assert result.efficiency_level == "highly_efficient"

    def test_analyze_file(self):
        """Test file analysis."""
        calculator = CARCalculator()
        
        # Test with non-existent file
        findings = calculator.analyze_file(Path("/nonexistent.py"))
        assert findings == []


class TestCoverageSignatureGenerator:
    """Test coverage signature generator functionality."""

    def test_signature_generator_initialization(self):
        """Test signature generator initialization."""
        generator = CoverageSignatureGenerator()
        assert generator._signatures == {}

    def test_generate_signature_hash(self):
        """Test signature hash generation."""
        generator = CoverageSignatureGenerator()
        
        coverage_data = CoverageData(
            test_name="test_example",
            file_path=Path("/tmp/test_example.py"),
            line_number=10,
            lines_covered=80,
            lines_total=100,
            branches_covered=40,
            branches_total=50,
            coverage_percentage=80.0,
            covered_lines={1, 2, 3},
            missing_lines={4, 5},
        )
        
        hash_result = generator._generate_signature_hash(coverage_data)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 32  # MD5 hash length

    def test_generate_signature_vector(self):
        """Test signature vector generation."""
        generator = CoverageSignatureGenerator()
        
        coverage_data = CoverageData(
            test_name="test_example",
            file_path=Path("/tmp/test_example.py"),
            line_number=10,
            lines_covered=80,
            lines_total=100,
            branches_covered=40,
            branches_total=50,
            coverage_percentage=80.0,
            covered_lines={1, 2, 3},
            missing_lines={4, 5},
        )
        
        vector = generator._generate_signature_vector(coverage_data)
        assert isinstance(vector, list)
        assert len(vector) > 0
        assert all(isinstance(x, float) for x in vector)

    def test_generate_coverage_pattern(self):
        """Test coverage pattern generation."""
        generator = CoverageSignatureGenerator()
        
        coverage_data = CoverageData(
            test_name="test_example",
            file_path=Path("/tmp/test_example.py"),
            line_number=10,
            lines_covered=80,
            lines_total=100,
            branches_covered=40,
            branches_total=50,
            coverage_percentage=80.0,
            covered_lines={1, 2, 3},
            missing_lines={4, 5},
        )
        
        pattern = generator._generate_coverage_pattern(coverage_data)
        assert isinstance(pattern, str)
        assert "coverage:80.0%" in pattern
        assert "lines:80/100" in pattern
        assert "branches:40/50" in pattern

    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        generator = CoverageSignatureGenerator()
        
        vector1 = [1.0, 2.0, 3.0]
        vector2 = [1.0, 2.0, 3.0]
        
        similarity = generator._cosine_similarity(vector1, vector2)
        assert similarity == 1.0  # Identical vectors
        
        vector3 = [0.0, 0.0, 0.0]
        similarity = generator._cosine_similarity(vector1, vector3)
        assert similarity == 0.0  # Orthogonal vectors

    def test_pattern_similarity(self):
        """Test pattern similarity calculation."""
        generator = CoverageSignatureGenerator()
        
        pattern1 = "coverage:80.0%|lines:80/100|branches:40/50"
        pattern2 = "coverage:80.0%|lines:80/100|branches:40/50"
        
        similarity = generator._pattern_similarity(pattern1, pattern2)
        assert similarity == 1.0  # Identical patterns
        
        pattern3 = "coverage:60.0%|lines:60/100|branches:30/50"
        similarity = generator._pattern_similarity(pattern1, pattern3)
        assert 0.0 <= similarity <= 1.0  # Some similarity

    def test_generate_signature(self):
        """Test complete signature generation."""
        generator = CoverageSignatureGenerator()
        
        coverage_data = CoverageData(
            test_name="test_example",
            file_path=Path("/tmp/test_example.py"),
            line_number=10,
            lines_covered=80,
            lines_total=100,
            branches_covered=40,
            branches_total=50,
            coverage_percentage=80.0,
            covered_lines={1, 2, 3},
            missing_lines={4, 5},
        )
        
        signature = generator.generate_signature(
            Path("/tmp/test_example.py"), "test_example", coverage_data
        )
        
        assert isinstance(signature, CoverageSignature)
        assert signature.test_name == "test_example"
        assert signature.signature_hash != ""
        assert len(signature.signature_vector) > 0
        assert signature.coverage_pattern != ""

    def test_calculate_similarity(self):
        """Test similarity calculation between signatures."""
        generator = CoverageSignatureGenerator()
        
        # Create two identical signatures
        coverage_data1 = CoverageData(
            test_name="test_example1",
            file_path=Path("/tmp/test_example1.py"),
            line_number=10,
            lines_covered=80,
            lines_total=100,
            branches_covered=40,
            branches_total=50,
            coverage_percentage=80.0,
            covered_lines={1, 2, 3},
            missing_lines={4, 5},
        )
        
        coverage_data2 = CoverageData(
            test_name="test_example2",
            file_path=Path("/tmp/test_example2.py"),
            line_number=10,
            lines_covered=80,
            lines_total=100,
            branches_covered=40,
            branches_total=50,
            coverage_percentage=80.0,
            covered_lines={1, 2, 3},
            missing_lines={4, 5},
        )
        
        signature1 = generator.generate_signature(
            Path("/tmp/test_example1.py"), "test_example1", coverage_data1
        )
        
        signature2 = generator.generate_signature(
            Path("/tmp/test_example2.py"), "test_example2", coverage_data2
        )
        
        similarity = generator.calculate_similarity(signature1, signature2)
        assert 0.0 <= similarity <= 1.0

    def test_find_similar_tests(self):
        """Test finding similar tests."""
        generator = CoverageSignatureGenerator()
        
        # Create a signature
        coverage_data = CoverageData(
            test_name="test_example",
            file_path=Path("/tmp/test_example.py"),
            line_number=10,
            lines_covered=80,
            lines_total=100,
            branches_covered=40,
            branches_total=50,
            coverage_percentage=80.0,
            covered_lines={1, 2, 3},
            missing_lines={4, 5},
        )
        
        signature = generator.generate_signature(
            Path("/tmp/test_example.py"), "test_example", coverage_data
        )
        
        similar_tests = generator.find_similar_tests(signature, threshold=0.8)
        assert isinstance(similar_tests, list)

    def test_analyze_file(self):
        """Test file analysis."""
        generator = CoverageSignatureGenerator()
        
        # Test with non-existent file
        findings = generator.analyze_file(Path("/nonexistent.py"))
        assert findings == []


class TestCoverageIntegration:
    """Test coverage integration functionality."""

    def test_coverage_data_structure(self):
        """Test coverage data structure."""
        coverage_data = CoverageData(
            test_name="test_example",
            file_path=Path("/tmp/test_example.py"),
            line_number=10,
            lines_covered=80,
            lines_total=100,
            branches_covered=40,
            branches_total=50,
            coverage_percentage=80.0,
            covered_lines={1, 2, 3},
            missing_lines={4, 5},
            coverage_signature="test_signature",
        )
        
        assert coverage_data.test_name == "test_example"
        assert coverage_data.coverage_percentage == 80.0
        assert len(coverage_data.covered_lines) == 3
        assert len(coverage_data.missing_lines) == 2

    def test_car_result_structure(self):
        """Test CAR result structure."""
        car_result = CARResult(
            test_name="test_example",
            file_path=Path("/tmp/test_example.py"),
            line_number=10,
            assertion_count=5,
            coverage_percentage=80.0,
            car_score=16.0,
            car_grade="F",
            efficiency_level="inefficient",
        )
        
        assert car_result.test_name == "test_example"
        assert car_result.assertion_count == 5
        assert car_result.car_score == 16.0
        assert car_result.car_grade == "F"

    def test_coverage_signature_structure(self):
        """Test coverage signature structure."""
        signature = CoverageSignature(
            test_name="test_example",
            file_path=Path("/tmp/test_example.py"),
            signature_hash="test_hash",
            signature_vector=[0.8, 0.8, 0.8],
            coverage_pattern="test_pattern",
            similarity_threshold=0.8,
        )
        
        assert signature.test_name == "test_example"
        assert signature.signature_hash == "test_hash"
        assert len(signature.signature_vector) == 3
        assert signature.similarity_threshold == 0.8
