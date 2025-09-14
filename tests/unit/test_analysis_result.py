"""Tests for analysis result models."""

from ast import AST
from datetime import datetime
from pathlib import Path

from pytest_drill_sergeant.core.analysis_result import (
    AAAComment,
    ASTAnalysisResult,
    ComprehensiveAnalysisResult,
    CoverageAnalysisResult,
    DuplicateAnalysisResult,
    FixtureAnalysisResult,
    FixtureCandidate,
    LiteralDifference,
    MockCall,
    ParameterCandidate,
    ParametrizationAnalysisResult,
    PrivateAccessViolation,
    RepeatedBlock,
    SimilarTest,
    StructuralEqualityCheck,
    SuggestedFixture,
)
from pytest_drill_sergeant.core.models import FeaturesData, Finding, RuleType, Severity

# Test constants to avoid magic numbers
ASSERTION_COUNT = 3
SIMILARITY_SCORE = 0.85
LINE_NUMBER_40 = 40
CONFIDENCE_95 = 0.95
CONSOLIDATION_SCORE = 0.8
START_LINE_10 = 10
END_LINE_15 = 15
OCCURRENCES_3 = 3
COMPLEXITY_REDUCTION = 0.3
EXTRACTION_SCORE = 0.8
COMPLEXITY_REDUCTION_2 = 0.4
LINE_NUMBER_5 = 5
ANALYSIS_TIME = 1.5
LINE_NUMBER_10 = 10
LINE_NUMBER_15 = 15
LINE_NUMBER_20 = 20
LINE_NUMBER_30 = 30
LINE_NUMBER_35 = 35
CYCLOMATIC_COMPLEXITY = 5
LINE_COUNT = 50
COMMENT_COUNT = 10
COVERAGE_PERCENTAGE = 85.5


class TestPrivateAccessViolation:
    """Test PrivateAccessViolation model."""

    def test_creation_with_required_fields(self) -> None:
        """Test creating a PrivateAccessViolation with required fields."""
        violation = PrivateAccessViolation(
            line_number=10,
            attribute_name="_private_attr",
            violation_type="private_attr",
            context="",
        )
        assert violation.line_number == LINE_NUMBER_10
        assert violation.attribute_name == "_private_attr"
        assert violation.violation_type == "private_attr"
        assert violation.context == ""

    def test_creation_with_all_fields(self) -> None:
        """Test creating a PrivateAccessViolation with all fields."""
        violation = PrivateAccessViolation(
            line_number=15,
            attribute_name="_private_method",
            violation_type="private_method",
            context="test_method",
        )
        assert violation.line_number == LINE_NUMBER_15
        assert violation.attribute_name == "_private_method"
        assert violation.violation_type == "private_method"
        assert violation.context == "test_method"


class TestMockCall:
    """Test MockCall model."""

    def test_creation_with_required_fields(self) -> None:
        """Test creating a MockCall with required fields."""
        mock_call = MockCall(
            line_number=20, mock_name="mock_obj", method_called="assert_called_once"
        )
        assert mock_call.line_number == LINE_NUMBER_20
        assert mock_call.mock_name == "mock_obj"
        assert mock_call.method_called == "assert_called_once"
        assert mock_call.arguments == []

    def test_creation_with_arguments(self) -> None:
        """Test creating a MockCall with arguments."""
        mock_call = MockCall(
            line_number=25,
            mock_name="mock_service",
            method_called="assert_called_with",
            arguments=["arg1", "arg2"],
        )
        assert mock_call.arguments == ["arg1", "arg2"]


class TestStructuralEqualityCheck:
    """Test StructuralEqualityCheck model."""

    def test_creation(self) -> None:
        """Test creating a StructuralEqualityCheck."""
        check = StructuralEqualityCheck(
            line_number=30,
            comparison_type="dict",
            left_operand="expected_dict",
            right_operand="actual_dict",
        )
        assert check.line_number == LINE_NUMBER_30
        assert check.comparison_type == "dict"
        assert check.left_operand == "expected_dict"
        assert check.right_operand == "actual_dict"


class TestAAAComment:
    """Test AAAComment model."""

    def test_creation(self) -> None:
        """Test creating an AAAComment."""
        comment = AAAComment(
            line_number=35, comment_type="arrange", content="Set up test data"
        )
        assert comment.line_number == LINE_NUMBER_35
        assert comment.comment_type == "arrange"
        assert comment.content == "Set up test data"


class TestASTAnalysisResult:
    """Test ASTAnalysisResult model."""

    def test_creation_with_required_fields(self) -> None:
        """Test creating an ASTAnalysisResult with required fields."""
        result = ASTAnalysisResult(
            test_name="test_example", file_path="/path/to/test.py"
        )
        assert result.test_name == "test_example"
        assert result.file_path == "/path/to/test.py"
        assert result.ast_node is None
        assert result.function_definitions == []
        assert result.class_definitions == []
        assert result.imports == []
        assert result.private_accesses == []
        assert result.mock_calls == []
        assert result.structural_equality_checks == []
        assert result.aaa_comments == []
        assert result.cyclomatic_complexity == 0
        assert result.line_count == 0
        assert result.comment_count == 0

    def test_creation_with_all_fields(self) -> None:
        """Test creating an ASTAnalysisResult with all fields."""
        mock_ast = AST()
        violation = PrivateAccessViolation(
            line_number=10, attribute_name="_private", violation_type="private_attr"
        )
        mock_call = MockCall(
            line_number=15, mock_name="mock_obj", method_called="assert_called"
        )

        result = ASTAnalysisResult(
            test_name="test_comprehensive",
            file_path="/path/to/test.py",
            ast_node=mock_ast,
            function_definitions=["test_function"],
            class_definitions=["TestClass"],
            imports=["pytest", "unittest.mock"],
            private_accesses=[violation],
            mock_calls=[mock_call],
            cyclomatic_complexity=5,
            line_count=50,
            comment_count=10,
        )
        assert result.ast_node is mock_ast
        assert result.function_definitions == ["test_function"]
        assert result.class_definitions == ["TestClass"]
        assert result.imports == ["pytest", "unittest.mock"]
        assert len(result.private_accesses) == 1
        assert len(result.mock_calls) == 1
        assert result.cyclomatic_complexity == CYCLOMATIC_COMPLEXITY
        assert result.line_count == LINE_COUNT
        assert result.comment_count == COMMENT_COUNT


class TestCoverageAnalysisResult:
    """Test CoverageAnalysisResult model."""

    def test_creation_with_required_fields(self) -> None:
        """Test creating a CoverageAnalysisResult with required fields."""
        result = CoverageAnalysisResult(
            test_name="test_coverage", file_path="/path/to/test.py"
        )
        assert result.test_name == "test_coverage"
        assert result.file_path == "/path/to/test.py"
        assert result.coverage_percentage == 0.0
        assert result.covered_lines == set()
        assert result.uncovered_lines == set()
        assert result.coverage_signature == ""
        assert result.assertion_count == 0
        assert result.assertion_types == {}
        assert result.mock_assertion_count == 0
        assert result.mock_calls == []

    def test_creation_with_coverage_data(self) -> None:
        """Test creating a CoverageAnalysisResult with coverage data."""
        result = CoverageAnalysisResult(
            test_name="test_coverage",
            file_path="/path/to/test.py",
            coverage_percentage=85.5,
            covered_lines={1, 2, 3, 5, 8},
            uncovered_lines={4, 6, 7},
            coverage_signature="abc123",
            assertion_count=3,
            assertion_types={"assert_equal": 2, "assert_true": 1},
            mock_assertion_count=1,
        )
        assert result.coverage_percentage == COVERAGE_PERCENTAGE
        assert result.covered_lines == {1, 2, 3, 5, 8}
        assert result.uncovered_lines == {4, 6, 7}
        assert result.coverage_signature == "abc123"
        assert result.assertion_count == ASSERTION_COUNT
        assert result.assertion_types == {"assert_equal": 2, "assert_true": 1}
        assert result.mock_assertion_count == 1


class TestSimilarTest:
    """Test SimilarTest model."""

    def test_creation(self) -> None:
        """Test creating a SimilarTest."""
        similar = SimilarTest(
            test_name="test_similar",
            file_path="/path/to/similar.py",
            similarity_score=0.85,
            similarity_type="ast",
        )
        assert similar.test_name == "test_similar"
        assert similar.file_path == "/path/to/similar.py"
        assert similar.similarity_score == SIMILARITY_SCORE
        assert similar.similarity_type == "ast"


class TestDuplicateAnalysisResult:
    """Test DuplicateAnalysisResult model."""

    def test_creation_with_required_fields(self) -> None:
        """Test creating a DuplicateAnalysisResult with required fields."""
        result = DuplicateAnalysisResult(
            test_name="test_duplicate", file_path="/path/to/test.py"
        )
        assert result.test_name == "test_duplicate"
        assert result.file_path == "/path/to/test.py"
        assert result.similar_tests == []
        assert result.similarity_scores == {}
        assert result.is_duplicate is False
        assert result.duplicate_cluster_id is None
        assert result.ast_similarity == {}
        assert result.simhash is None
        assert result.coverage_similarity == {}
        assert result.jaccard_index == {}

    def test_creation_with_similarity_data(self) -> None:
        """Test creating a DuplicateAnalysisResult with similarity data."""
        similar_test = SimilarTest(
            test_name="test_similar",
            file_path="/path/to/similar.py",
            similarity_score=0.9,
            similarity_type="ast",
        )

        result = DuplicateAnalysisResult(
            test_name="test_duplicate",
            file_path="/path/to/test.py",
            similar_tests=[similar_test],
            similarity_scores={"test_similar": 0.9},
            is_duplicate=True,
            duplicate_cluster_id="cluster_1",
            ast_similarity={"test_similar": 0.9},
            simhash="abc123",
            coverage_similarity={"test_similar": 0.85},
            jaccard_index={"test_similar": 0.8},
        )
        assert len(result.similar_tests) == 1
        assert result.similarity_scores == {"test_similar": 0.9}
        assert result.is_duplicate is True
        assert result.duplicate_cluster_id == "cluster_1"
        assert result.ast_similarity == {"test_similar": 0.9}
        assert result.simhash == "abc123"
        assert result.coverage_similarity == {"test_similar": 0.85}
        assert result.jaccard_index == {"test_similar": 0.8}


class TestLiteralDifference:
    """Test LiteralDifference model."""

    def test_creation(self) -> None:
        """Test creating a LiteralDifference."""
        diff = LiteralDifference(
            line_number=40,
            variable_name="expected_value",
            values=["value1", "value2", "value3"],
            suggested_parameter="test_value",
        )
        assert diff.line_number == LINE_NUMBER_40
        assert diff.variable_name == "expected_value"
        assert diff.values == ["value1", "value2", "value3"]
        assert diff.suggested_parameter == "test_value"


class TestParameterCandidate:
    """Test ParameterCandidate model."""

    def test_creation(self) -> None:
        """Test creating a ParameterCandidate."""
        candidate = ParameterCandidate(
            parameter_name="test_data",
            values=["data1", "data2"],
            line_numbers=[10, 20, 30],
            confidence=0.95,
        )
        assert candidate.parameter_name == "test_data"
        assert candidate.values == ["data1", "data2"]
        assert candidate.line_numbers == [10, 20, 30]
        assert candidate.confidence == CONFIDENCE_95


class TestParametrizationAnalysisResult:
    """Test ParametrizationAnalysisResult model."""

    def test_creation_with_required_fields(self) -> None:
        """Test creating a ParametrizationAnalysisResult with required fields."""
        result = ParametrizationAnalysisResult(
            test_name="test_parametrize", file_path="/path/to/test.py"
        )
        assert result.test_name == "test_parametrize"
        assert result.file_path == "/path/to/test.py"
        assert result.literal_differences == []
        assert result.parameter_candidates == []
        assert result.suggested_parameters == []
        assert result.similar_tests == []
        assert result.consolidation_score == 0.0
        assert result.parametrize_decorator is None
        assert result.consolidated_test is None

    def test_creation_with_parametrization_data(self) -> None:
        """Test creating a ParametrizationAnalysisResult with parametrization data."""
        literal_diff = LiteralDifference(
            line_number=10,
            variable_name="value",
            values=["a", "b"],
            suggested_parameter="test_value",
        )
        param_candidate = ParameterCandidate(
            parameter_name="test_value",
            values=["a", "b"],
            line_numbers=[10, 20],
            confidence=0.9,
        )

        result = ParametrizationAnalysisResult(
            test_name="test_parametrize",
            file_path="/path/to/test.py",
            literal_differences=[literal_diff],
            parameter_candidates=[param_candidate],
            suggested_parameters=["test_value"],
            similar_tests=["test_similar"],
            consolidation_score=0.8,
            parametrize_decorator="@pytest.mark.parametrize('test_value', ['a', 'b'])",
            consolidated_test="def test_consolidated(test_value): ...",
        )
        assert len(result.literal_differences) == 1
        assert len(result.parameter_candidates) == 1
        assert result.suggested_parameters == ["test_value"]
        assert result.similar_tests == ["test_similar"]
        assert result.consolidation_score == CONSOLIDATION_SCORE
        assert result.parametrize_decorator is not None
        assert result.consolidated_test is not None


class TestRepeatedBlock:
    """Test RepeatedBlock model."""

    def test_creation(self) -> None:
        """Test creating a RepeatedBlock."""
        block = RepeatedBlock(
            start_line=10,
            end_line=15,
            code="def setup_data():\n    return {'key': 'value'}",
            occurrences=3,
            test_names=["test1", "test2", "test3"],
        )
        assert block.start_line == START_LINE_10
        assert block.end_line == END_LINE_15
        assert "def setup_data():" in block.code
        assert block.occurrences == OCCURRENCES_3
        assert block.test_names == ["test1", "test2", "test3"]


class TestFixtureCandidate:
    """Test FixtureCandidate model."""

    def test_creation(self) -> None:
        """Test creating a FixtureCandidate."""
        candidate = FixtureCandidate(
            fixture_name="test_data",
            code="@pytest.fixture\ndef test_data():\n    return {'key': 'value'}",
            parameters=["param1", "param2"],
            return_type="dict",
            complexity_reduction=0.3,
        )
        assert candidate.fixture_name == "test_data"
        assert "@pytest.fixture" in candidate.code
        assert candidate.parameters == ["param1", "param2"]
        assert candidate.return_type == "dict"
        assert candidate.complexity_reduction == COMPLEXITY_REDUCTION


class TestSuggestedFixture:
    """Test SuggestedFixture model."""

    def test_creation(self) -> None:
        """Test creating a SuggestedFixture."""
        fixture = SuggestedFixture(
            fixture_name="mock_service",
            description="Mock service for testing",
            parameters=["service_name"],
            code="@pytest.fixture\ndef mock_service(service_name): ...",
            usage_example="def test_with_mock(mock_service): ...",
        )
        assert fixture.fixture_name == "mock_service"
        assert fixture.description == "Mock service for testing"
        assert fixture.parameters == ["service_name"]
        assert "@pytest.fixture" in fixture.code
        assert "def test_with_mock" in fixture.usage_example


class TestFixtureAnalysisResult:
    """Test FixtureAnalysisResult model."""

    def test_creation_with_required_fields(self) -> None:
        """Test creating a FixtureAnalysisResult with required fields."""
        result = FixtureAnalysisResult(
            test_name="test_fixture", file_path="/path/to/test.py"
        )
        assert result.test_name == "test_fixture"
        assert result.file_path == "/path/to/test.py"
        assert result.repeated_blocks == []
        assert result.fixture_candidates == []
        assert result.suggested_fixtures == []
        assert result.fixture_code == []
        assert result.refactored_test is None
        assert result.extraction_score == 0.0
        assert result.complexity_reduction == 0.0

    def test_creation_with_fixture_data(self) -> None:
        """Test creating a FixtureAnalysisResult with fixture data."""
        repeated_block = RepeatedBlock(
            start_line=10,
            end_line=15,
            code="setup code",
            occurrences=2,
            test_names=["test1", "test2"],
        )
        fixture_candidate = FixtureCandidate(
            fixture_name="test_fixture",
            code="fixture code",
            parameters=[],
            return_type="str",
            complexity_reduction=0.5,
        )
        suggested_fixture = SuggestedFixture(
            fixture_name="suggested_fixture",
            description="A suggested fixture",
            parameters=[],
            code="suggested code",
            usage_example="usage example",
        )

        result = FixtureAnalysisResult(
            test_name="test_fixture",
            file_path="/path/to/test.py",
            repeated_blocks=[repeated_block],
            fixture_candidates=[fixture_candidate],
            suggested_fixtures=[suggested_fixture],
            fixture_code=["fixture1", "fixture2"],
            refactored_test="refactored test code",
            extraction_score=0.8,
            complexity_reduction=0.4,
        )
        assert len(result.repeated_blocks) == 1
        assert len(result.fixture_candidates) == 1
        assert len(result.suggested_fixtures) == 1
        assert result.fixture_code == ["fixture1", "fixture2"]
        assert result.refactored_test == "refactored test code"
        assert result.extraction_score == EXTRACTION_SCORE
        assert result.complexity_reduction == COMPLEXITY_REDUCTION_2


class TestComprehensiveAnalysisResult:
    """Test ComprehensiveAnalysisResult model."""

    def test_creation_with_required_fields(self) -> None:
        """Test creating a ComprehensiveAnalysisResult with required fields."""
        features = FeaturesData(
            test_name="test_comprehensive",
            file_path=Path("/path/to/test.py"),
            line_number=5,
            has_aaa_comments=True,
            aaa_comment_order="arrange_act_assert",
            private_access_count=0,
            mock_assertion_count=0,
            structural_equality_count=0,
            test_length=10,
            complexity_score=1.0,
            coverage_percentage=85.0,
            coverage_signature="test_signature",
            assertion_count=3,
            setup_lines=2,
            teardown_lines=1,
            execution_time=0.1,
            memory_usage=1.0,
            exception_count=0,
        )

        result = ComprehensiveAnalysisResult(
            test_name="test_comprehensive",
            file_path="/path/to/test.py",
            line_number=5,
            features=features,
        )
        assert result.test_name == "test_comprehensive"
        assert result.file_path == "/path/to/test.py"
        assert result.line_number == LINE_NUMBER_5
        assert result.features is features
        assert result.ast_result is None
        assert result.coverage_result is None
        assert result.duplicate_result is None
        assert result.parametrization_result is None
        assert result.fixture_result is None
        assert result.all_findings == []
        assert result.analysis_time == 0.0
        assert result.analysis_errors == []
        assert isinstance(result.created_at, datetime)

    def test_creation_with_analysis_results(self) -> None:
        """Test creating a ComprehensiveAnalysisResult with analysis results."""
        features = FeaturesData(
            test_name="test_comprehensive",
            file_path=Path("/path/to/test.py"),
            line_number=5,
            has_aaa_comments=True,
            aaa_comment_order="arrange_act_assert",
            private_access_count=0,
            mock_assertion_count=0,
            structural_equality_count=0,
            test_length=20,
            complexity_score=2.0,
            coverage_percentage=90.0,
            coverage_signature="test_signature_2",
            assertion_count=5,
            setup_lines=3,
            teardown_lines=2,
            execution_time=0.2,
            memory_usage=1.5,
            exception_count=0,
        )

        ast_result = ASTAnalysisResult(
            test_name="test_ast", file_path="/path/to/test.py"
        )
        coverage_result = CoverageAnalysisResult(
            test_name="test_coverage", file_path="/path/to/test.py"
        )
        finding = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            message="Test finding",
            severity=Severity.ERROR,
            file_path=Path("/path/to/test.py"),
            line_number=10,
            column_number=5,
            code_snippet="test code",
            suggestion="fix suggestion",
            confidence=0.9,
        )

        result = ComprehensiveAnalysisResult(
            test_name="test_comprehensive",
            file_path="/path/to/test.py",
            line_number=5,
            features=features,
            ast_result=ast_result,
            coverage_result=coverage_result,
            all_findings=[finding],
            analysis_time=1.5,
            analysis_errors=["error1", "error2"],
        )
        assert result.ast_result is ast_result
        assert result.coverage_result is coverage_result
        assert len(result.all_findings) == 1
        assert result.analysis_time == ANALYSIS_TIME
        assert result.analysis_errors == ["error1", "error2"]
