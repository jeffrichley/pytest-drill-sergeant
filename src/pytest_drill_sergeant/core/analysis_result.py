"""Analysis result models for specific analysis types."""

from __future__ import annotations

from ast import AST
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from pytest_drill_sergeant.core.models import FeaturesData, Finding


class PrivateAccessViolation(BaseModel):
    """A private attribute or method access violation."""

    line_number: int = Field(..., description="Line number of the violation")
    attribute_name: str = Field(
        ..., description="Name of the private attribute accessed"
    )
    violation_type: str = Field(
        ..., description="Type of violation (e.g., 'private_method', 'private_attr')"
    )
    context: str = Field("", description="Context where the violation occurred")


class MockCall(BaseModel):
    """A mock call found in the test."""

    line_number: int = Field(..., description="Line number of the mock call")
    mock_name: str = Field(..., description="Name of the mock object")
    method_called: str = Field(..., description="Method being called on the mock")
    arguments: list[str] = Field(
        default_factory=list, description="Arguments passed to the mock method"
    )


class StructuralEqualityCheck(BaseModel):
    """A structural equality comparison found in the test."""

    line_number: int = Field(..., description="Line number of the equality check")
    comparison_type: str = Field(
        ..., description="Type of comparison (e.g., 'dict', 'list', 'set')"
    )
    left_operand: str = Field(..., description="Left side of the comparison")
    right_operand: str = Field(..., description="Right side of the comparison")


class AAAComment(BaseModel):
    """An AAA (Arrange, Act, Assert) comment found in the test."""

    line_number: int = Field(..., description="Line number of the comment")
    comment_type: str = Field(
        ..., description="Type of AAA comment (arrange, act, assert)"
    )
    content: str = Field(..., description="Content of the comment")


class ASTAnalysisResult(BaseModel):
    """Result of AST-based analysis."""

    test_name: str = Field(..., description="Name of the test being analyzed")
    file_path: str = Field(..., description="Path to the test file")

    # AST features
    ast_node: AST | None = Field(None, description="Root AST node of the test")
    function_definitions: list[str] = Field(
        default_factory=list, description="Function definitions found"
    )
    class_definitions: list[str] = Field(
        default_factory=list, description="Class definitions found"
    )
    imports: list[str] = Field(default_factory=list, description="Import statements")

    # Analysis results
    private_accesses: list[PrivateAccessViolation] = Field(
        default_factory=list, description="Private access violations"
    )
    mock_calls: list[MockCall] = Field(
        default_factory=list, description="Mock calls found"
    )
    structural_equality_checks: list[StructuralEqualityCheck] = Field(
        default_factory=list, description="Structural equality checks"
    )
    aaa_comments: list[AAAComment] = Field(
        default_factory=list, description="AAA comments found"
    )

    # Complexity metrics
    cyclomatic_complexity: int = Field(0, description="Cyclomatic complexity")
    line_count: int = Field(0, description="Total line count")
    comment_count: int = Field(0, description="Comment line count")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class CoverageAnalysisResult(BaseModel):
    """Result of coverage-based analysis."""

    test_name: str = Field(..., description="Name of the test being analyzed")
    file_path: str = Field(..., description="Path to the test file")

    # Coverage data
    coverage_percentage: float = Field(
        0.0, ge=0.0, le=100.0, description="Coverage percentage"
    )
    covered_lines: set[int] = Field(
        default_factory=set, description="Covered line numbers"
    )
    uncovered_lines: set[int] = Field(
        default_factory=set, description="Uncovered line numbers"
    )
    coverage_signature: str = Field("", description="Coverage signature for similarity")

    # Assertion analysis
    assertion_count: int = Field(0, description="Number of assertions")
    assertion_types: dict[str, int] = Field(
        default_factory=dict, description="Types of assertions used"
    )

    # Mock analysis
    mock_assertion_count: int = Field(0, description="Number of mock assertions")
    mock_calls: list[MockCall] = Field(
        default_factory=list, description="Mock calls made"
    )

    model_config = ConfigDict(
        use_enum_values=True,
    )


class SimilarTest(BaseModel):
    """A test that is similar to the current test."""

    test_name: str = Field(..., description="Name of the similar test")
    file_path: str = Field(..., description="Path to the similar test file")
    similarity_score: float = Field(..., description="Similarity score (0.0 to 1.0)")
    similarity_type: str = Field(
        ..., description="Type of similarity (ast, coverage, jaccard)"
    )


class DuplicateAnalysisResult(BaseModel):
    """Result of duplicate test analysis."""

    test_name: str = Field(..., description="Name of the test being analyzed")
    file_path: str = Field(..., description="Path to the test file")

    # Similarity data
    similar_tests: list[SimilarTest] = Field(
        default_factory=list, description="Similar tests found"
    )
    similarity_scores: dict[str, float] = Field(
        default_factory=dict, description="Similarity scores with other tests"
    )
    is_duplicate: bool = Field(False, description="Whether this test is a duplicate")
    duplicate_cluster_id: str | None = Field(
        None, description="ID of the duplicate cluster"
    )

    # Static similarity (AST-based)
    ast_similarity: dict[str, float] = Field(
        default_factory=dict, description="AST similarity scores"
    )
    simhash: str | None = Field(
        None, description="SimHash signature for fast comparison"
    )

    # Dynamic similarity (coverage-based)
    coverage_similarity: dict[str, float] = Field(
        default_factory=dict, description="Coverage similarity scores"
    )
    jaccard_index: dict[str, float] = Field(
        default_factory=dict, description="Jaccard similarity scores"
    )

    model_config = ConfigDict(
        validate_assignment=True,
    )


class LiteralDifference(BaseModel):
    """A literal difference found between similar tests."""

    line_number: int = Field(..., description="Line number where the difference occurs")
    variable_name: str = Field(..., description="Name of the variable that differs")
    values: list[str] = Field(..., description="Different values found across tests")
    suggested_parameter: str = Field(..., description="Suggested parameter name")


class ParameterCandidate(BaseModel):
    """A parameter that could be extracted from tests."""

    parameter_name: str = Field(..., description="Suggested name for the parameter")
    values: list[str] = Field(
        ..., description="Values that would be passed to this parameter"
    )
    line_numbers: list[int] = Field(
        ..., description="Line numbers where this parameter appears"
    )
    confidence: float = Field(
        ..., description="Confidence score for this parameter (0.0 to 1.0)"
    )


class ParametrizationAnalysisResult(BaseModel):
    """Result of parametrization analysis."""

    test_name: str = Field(..., description="Name of the test being analyzed")
    file_path: str = Field(..., description="Path to the test file")

    # Parametrization opportunities
    literal_differences: list[LiteralDifference] = Field(
        default_factory=list, description="Literal differences found"
    )
    parameter_candidates: list[ParameterCandidate] = Field(
        default_factory=list, description="Parameter candidates"
    )
    suggested_parameters: list[str] = Field(
        default_factory=list, description="Suggested parameter names"
    )

    # Test consolidation opportunities
    similar_tests: list[str] = Field(
        default_factory=list, description="Tests that could be consolidated"
    )
    consolidation_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Score for consolidation opportunity"
    )

    # Generated code
    parametrize_decorator: str | None = Field(
        None, description="Generated @pytest.mark.parametrize decorator"
    )
    consolidated_test: str | None = Field(
        None, description="Generated consolidated test code"
    )

    model_config = ConfigDict(
        validate_assignment=True,
    )


class RepeatedBlock(BaseModel):
    """A repeated code block that could be extracted to a fixture."""

    start_line: int = Field(..., description="Starting line number of the block")
    end_line: int = Field(..., description="Ending line number of the block")
    code: str = Field(..., description="The repeated code content")
    occurrences: int = Field(..., description="Number of times this block appears")
    test_names: list[str] = Field(
        default_factory=list, description="Tests that contain this block"
    )


class FixtureCandidate(BaseModel):
    """A fixture that could be extracted from repeated code."""

    fixture_name: str = Field(..., description="Suggested name for the fixture")
    code: str = Field(..., description="Generated fixture code")
    parameters: list[str] = Field(
        default_factory=list, description="Parameters the fixture would take"
    )
    return_type: str = Field(..., description="Type of object the fixture returns")
    complexity_reduction: float = Field(
        ..., description="Expected complexity reduction from this fixture"
    )


class SuggestedFixture(BaseModel):
    """A suggested fixture with metadata."""

    fixture_name: str = Field(..., description="Name of the suggested fixture")
    description: str = Field(..., description="Description of what the fixture does")
    parameters: list[str] = Field(
        default_factory=list, description="Parameters for the fixture"
    )
    code: str = Field(..., description="Generated fixture code")
    usage_example: str = Field(..., description="Example of how to use the fixture")


class FixtureAnalysisResult(BaseModel):
    """Result of fixture extraction analysis."""

    test_name: str = Field(..., description="Name of the test being analyzed")
    file_path: str = Field(..., description="Path to the test file")

    # Fixture opportunities
    repeated_blocks: list[RepeatedBlock] = Field(
        default_factory=list, description="Repeated code blocks found"
    )
    fixture_candidates: list[FixtureCandidate] = Field(
        default_factory=list, description="Fixture candidates"
    )
    suggested_fixtures: list[SuggestedFixture] = Field(
        default_factory=list, description="Suggested fixtures"
    )

    # Code generation
    fixture_code: list[str] = Field(
        default_factory=list, description="Generated fixture code"
    )
    refactored_test: str | None = Field(None, description="Refactored test code")

    # Analysis metadata
    extraction_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Score for fixture extraction opportunity"
    )
    complexity_reduction: float = Field(
        0.0, description="Expected complexity reduction"
    )

    model_config = ConfigDict(
        validate_assignment=True,
    )


class ComprehensiveAnalysisResult(BaseModel):
    """Comprehensive analysis result combining all analysis types."""

    test_name: str = Field(..., description="Name of the test being analyzed")
    file_path: str = Field(..., description="Path to the test file")
    line_number: int = Field(..., description="Line number where the test starts")

    # Individual analysis results
    ast_result: ASTAnalysisResult | None = Field(
        None, description="AST analysis result"
    )
    coverage_result: CoverageAnalysisResult | None = Field(
        None, description="Coverage analysis result"
    )
    duplicate_result: DuplicateAnalysisResult | None = Field(
        None, description="Duplicate analysis result"
    )
    parametrization_result: ParametrizationAnalysisResult | None = Field(
        None, description="Parametrization analysis result"
    )
    fixture_result: FixtureAnalysisResult | None = Field(
        None, description="Fixture analysis result"
    )

    # Aggregated findings
    all_findings: list[Finding] = Field(
        default_factory=list, description="All findings from all analyses"
    )
    features: FeaturesData = Field(..., description="Aggregated test features")

    # Analysis metadata
    analysis_time: float = Field(0.0, description="Total analysis time in seconds")
    analysis_errors: list[str] = Field(
        default_factory=list, description="Errors encountered during analysis"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="When this analysis was created"
    )

    model_config = ConfigDict(
        validate_assignment=True,
    )
