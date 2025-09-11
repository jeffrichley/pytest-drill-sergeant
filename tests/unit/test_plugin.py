"""Unit tests for the drill sergeant plugin functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from _pytest.outcomes import Failed

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.models import ValidationIssue
from pytest_drill_sergeant.utils import detect_test_type_from_path
from pytest_drill_sergeant.validators.aaa import (
    AAAValidator,
    _build_aaa_keyword_lists,
    _has_descriptive_comment,
    _validate_aaa_structure,
)
from pytest_drill_sergeant.validators.error_reporter import _report_all_issues
from pytest_drill_sergeant.validators.marker import _validate_markers


@pytest.mark.unit
class TestValidationIssue:
    """Test the ValidationIssue dataclass."""

    def test_validation_issue_creation(self) -> None:
        """# Arrange - ValidationIssue with all fields
        # Act - Create a ValidationIssue instance
        # Assert - All fields are properly set
        """
        # Arrange - ValidationIssue with all required fields
        issue_type = "marker"
        message = "Test message"
        suggestion = "Test suggestion"

        # Act - Create ValidationIssue instance
        issue = ValidationIssue(
            issue_type=issue_type, message=message, suggestion=suggestion
        )

        # Assert - All fields are correctly set
        assert issue.issue_type == issue_type
        assert issue.message == message
        assert issue.suggestion == suggestion


@pytest.mark.unit
@patch("pytest_drill_sergeant.utils.helpers.get_available_markers")
class TestDetectTestTypeFromPath:
    """Test test type detection from file paths."""

    def test_detect_unit_test_from_path(self, mock_get_markers: Mock) -> None:
        """# Arrange - Mock pytest item with unit test path
        # Act - Detect test type from path
        # Assert - Returns 'unit' marker
        """
        # Arrange - Mock item with unit test path
        mock_item = Mock()
        mock_item.fspath = Path("/project/tests/unit/test_example.py")
        mock_get_markers.return_value = {
            "unit",
            "integration",
            "functional",
            "e2e",
            "performance",
        }
        config = DrillSergeantConfig()

        # Act - Detect test type
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Returns unit marker
        assert result == "unit"

    def test_detect_integration_test_from_path(self, mock_get_markers: Mock) -> None:
        """# Arrange - Mock pytest item with integration test path
        # Act - Detect test type from path
        # Assert - Returns 'integration' marker
        """
        # Arrange - Mock item with integration test path
        mock_item = Mock()
        mock_item.fspath = Path("/project/tests/integration/test_api.py")
        mock_get_markers.return_value = {
            "unit",
            "integration",
            "functional",
            "e2e",
            "performance",
        }
        config = DrillSergeantConfig()

        # Act - Detect test type
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Returns integration marker
        assert result == "integration"

    def test_detect_functional_test_from_path(self, mock_get_markers: Mock) -> None:
        """# Arrange - Mock pytest item with functional test path
        # Act - Detect test type from path
        # Assert - Returns 'functional' marker
        """
        # Arrange - Mock item with functional test path
        mock_item = Mock()
        mock_item.fspath = Path("/project/tests/functional/test_workflow.py")
        mock_get_markers.return_value = {
            "unit",
            "integration",
            "functional",
            "e2e",
            "performance",
        }
        config = DrillSergeantConfig()

        # Act - Detect test type
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Returns functional marker
        assert result == "functional"

    def test_detect_e2e_test_from_path(self, mock_get_markers: Mock) -> None:
        """# Arrange - Mock pytest item with e2e test path
        # Act - Detect test type from path
        # Assert - Returns 'e2e' marker
        """
        # Arrange - Mock item with e2e test path
        mock_item = Mock()
        mock_item.fspath = Path("/project/tests/e2e/test_full_flow.py")
        mock_get_markers.return_value = {
            "unit",
            "integration",
            "functional",
            "e2e",
            "performance",
        }
        config = DrillSergeantConfig()

        # Act - Detect test type
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Returns e2e marker
        assert result == "e2e"

    def test_detect_performance_test_from_path(self, mock_get_markers: Mock) -> None:
        """# Arrange - Mock pytest item with performance test path
        # Act - Detect test type from path
        # Assert - Returns 'performance' marker
        """
        # Arrange - Mock item with performance test path
        mock_item = Mock()
        mock_item.fspath = Path("/project/tests/performance/test_load.py")
        mock_get_markers.return_value = {
            "unit",
            "integration",
            "functional",
            "e2e",
            "performance",
        }
        config = DrillSergeantConfig()

        # Act - Detect test type
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Returns performance marker
        assert result == "performance"

    def test_detect_fixtures_as_unit_from_path(self, mock_get_markers: Mock) -> None:
        """# Arrange - Mock pytest item with fixtures test path
        # Act - Detect test type from path
        # Assert - Returns 'unit' marker for fixtures
        """
        # Arrange - Mock item with fixtures test path
        mock_item = Mock()
        mock_item.fspath = Path("/project/tests/fixtures/test_data.py")
        mock_get_markers.return_value = {
            "unit",
            "integration",
            "functional",
            "e2e",
            "performance",
        }
        config = DrillSergeantConfig()

        # Act - Detect test type
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Returns unit marker for fixtures
        assert result == "unit"

    def test_detect_unknown_test_type_returns_none(
        self, mock_get_markers: Mock
    ) -> None:
        """# Arrange - Mock pytest item with unknown test path
        # Act - Detect test type from path
        # Assert - Returns None for unknown type
        """
        # Arrange - Mock item with unknown test path
        mock_item = Mock()
        mock_item.fspath = Path("/project/tests/unknown/test_something.py")
        mock_get_markers.return_value = {
            "unit",
            "integration",
            "functional",
            "e2e",
            "performance",
        }
        config = DrillSergeantConfig()

        # Act - Detect test type
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Returns None for unknown type
        assert result is None

    def test_detect_no_tests_directory_returns_none(
        self, mock_get_markers: Mock
    ) -> None:
        """# Arrange - Mock pytest item with no tests directory
        # Act - Detect test type from path
        # Assert - Returns None when no tests directory
        """
        # Arrange - Mock item with no tests directory
        mock_item = Mock()
        mock_item.fspath = Path("/project/src/test_module.py")
        mock_get_markers.return_value = {
            "unit",
            "integration",
            "functional",
            "e2e",
            "performance",
        }
        config = DrillSergeantConfig()

        # Act - Detect test type
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Returns None when no tests directory
        assert result is None

    def test_detect_exception_handling_returns_none(
        self, mock_get_markers: Mock
    ) -> None:
        """# Arrange - Mock pytest item that raises exception
        # Act - Detect test type from path
        # Assert - Returns None when exception occurs
        """
        # Arrange - Mock item that raises exception
        mock_item = Mock()
        mock_item.fspath = Mock(side_effect=Exception("Test exception"))
        mock_get_markers.return_value = {
            "unit",
            "integration",
            "functional",
            "e2e",
            "performance",
        }
        config = DrillSergeantConfig()

        # Act - Detect test type
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Returns None when exception occurs
        assert result is None


@pytest.mark.unit
class TestHasDescriptiveComment:
    """Test descriptive comment validation."""

    def test_valid_descriptive_comment(self) -> None:
        """# Arrange - Comment line with proper dash and description
        # Act - Check if comment is descriptive
        # Assert - Returns True for valid descriptive comment
        """
        # Arrange - Comment with proper format
        comment_line = "# Arrange - Set up test data and mocks"

        # Act - Check if descriptive
        result = _has_descriptive_comment(comment_line)

        # Assert - Returns True for valid comment
        assert result is True

    def test_comment_without_dash_returns_false(self) -> None:
        """# Arrange - Comment line without descriptive dash
        # Act - Check if comment is descriptive
        # Assert - Returns False for comment without dash
        """
        # Arrange - Comment without dash
        comment_line = "# Arrange setup code"

        # Act - Check if descriptive
        result = _has_descriptive_comment(comment_line)

        # Assert - Returns False for no dash
        assert result is False

    def test_comment_with_short_description_returns_false(self) -> None:
        """# Arrange - Comment line with too short description
        # Act - Check if comment is descriptive
        # Assert - Returns False for short description
        """
        # Arrange - Comment with short description
        comment_line = "# Act - Do"

        # Act - Check if descriptive
        result = _has_descriptive_comment(comment_line)

        # Assert - Returns False for short description
        assert result is False

    def test_comment_with_empty_description_returns_false(self) -> None:
        """# Arrange - Comment line with empty description after dash
        # Act - Check if comment is descriptive
        # Assert - Returns False for empty description
        """
        # Arrange - Comment with empty description
        comment_line = "# Assert - "

        # Act - Check if descriptive
        result = _has_descriptive_comment(comment_line)

        # Assert - Returns False for empty description
        assert result is False


@pytest.mark.unit
class TestValidateMarkers:
    """Test marker validation functionality."""

    def test_validate_markers_with_existing_markers(self) -> None:
        """# Arrange - Mock pytest item with existing markers
        # Act - Validate markers on the item
        # Assert - Returns empty issues list
        """
        # Arrange - Mock item with existing markers
        mock_item = Mock()
        mock_item.iter_markers.return_value = [Mock()]  # Has markers
        config = DrillSergeantConfig()

        # Act - Validate markers
        issues = _validate_markers(mock_item, config)

        # Assert - No issues when markers exist
        assert issues == []

    def test_validate_markers_auto_detection_enabled_by_default(self) -> None:
        """# Arrange - Config with auto-detection enabled
        # Act - Check if auto-detection is enabled
        # Assert - Auto-detection is enabled by default
        """
        # Arrange - Default config
        config = DrillSergeantConfig()

        # Act & Assert - Auto-detection should be enabled by default
        assert config.auto_detect_markers is True

    @patch("pytest_drill_sergeant.utils.helpers.detect_test_type_from_path")
    def test_validate_markers_creates_issue_when_not_detectable(
        self, mock_detect: Mock
    ) -> None:
        """# Arrange - Mock pytest item without markers and not detectable
        # Act - Validate markers on the item
        # Assert - Creates marker validation issue
        """
        # Arrange - Mock item without markers and not detectable
        mock_item = Mock()
        mock_item.iter_markers.return_value = []  # No markers
        mock_item.name = "test_example"
        mock_detect.return_value = None
        config = DrillSergeantConfig()

        # Act - Validate markers
        issues = _validate_markers(mock_item, config)

        # Assert - Creates marker issue
        assert len(issues) == 1
        assert issues[0].issue_type == "marker"
        assert "test_example" in issues[0].message
        assert "must have at least one marker" in issues[0].message


@pytest.mark.unit
class TestValidateAaaStructure:
    """Test AAA structure validation."""

    @patch("pytest_drill_sergeant.validators.aaa.inspect.getsource")
    def test_validate_aaa_with_complete_structure(self, mock_getsource: Mock) -> None:
        """# Arrange - Mock function source with complete AAA structure
        # Act - Validate AAA structure
        # Assert - Returns no issues for complete structure
        """
        # Arrange - Complete AAA structure source
        mock_item = Mock()
        mock_item.name = "test_example"
        mock_getsource.return_value = """
def test_example():
    # Arrange - Set up test data and dependencies
    data = {"key": "value"}

    # Act - Execute the function under test
    result = process_data(data)

    # Assert - Verify the expected outcome
    assert result == expected_value
"""

        # Act - Validate AAA structure
        config = DrillSergeantConfig()
        issues = _validate_aaa_structure(mock_item, config)

        # Assert - No issues for complete structure
        assert issues == []

    @patch("pytest_drill_sergeant.validators.aaa.inspect.getsource")
    def test_validate_aaa_missing_arrange_section(self, mock_getsource: Mock) -> None:
        """# Arrange - Mock function source missing Arrange section
        # Act - Validate AAA structure
        # Assert - Returns issue for missing Arrange section
        """
        # Arrange - Source missing Arrange section
        mock_item = Mock()
        mock_item.name = "test_example"
        mock_getsource.return_value = """
def test_example():
    # Act - Execute the function under test
    result = process_data()

    # Assert - Verify the expected outcome
    assert result == expected_value
"""

        # Act - Validate AAA structure
        config = DrillSergeantConfig()
        issues = _validate_aaa_structure(mock_item, config)

        # Assert - Has issue for missing Arrange
        arrange_issues = [i for i in issues if "missing 'Arrange'" in i.message]
        assert len(arrange_issues) == 1
        assert arrange_issues[0].issue_type == "aaa"

    @patch("pytest_drill_sergeant.validators.aaa.inspect.getsource")
    def test_validate_aaa_missing_act_section(self, mock_getsource: Mock) -> None:
        """# Arrange - Mock function source missing Act section
        # Act - Validate AAA structure
        # Assert - Returns issue for missing Act section
        """
        # Arrange - Source missing Act section
        mock_item = Mock()
        mock_item.name = "test_example"
        mock_getsource.return_value = """
def test_example():
    # Arrange - Set up test data and dependencies
    data = {"key": "value"}

    # Assert - Verify the expected outcome
    assert result == expected_value
"""

        # Act - Validate AAA structure
        config = DrillSergeantConfig()
        issues = _validate_aaa_structure(mock_item, config)

        # Assert - Has issue for missing Act
        act_issues = [i for i in issues if "missing 'Act'" in i.message]
        assert len(act_issues) == 1
        assert act_issues[0].issue_type == "aaa"

    @patch("pytest_drill_sergeant.validators.aaa.inspect.getsource")
    def test_validate_aaa_missing_assert_section(self, mock_getsource: Mock) -> None:
        """# Arrange - Mock function source missing Assert section
        # Act - Validate AAA structure
        # Assert - Returns issue for missing Assert section
        """
        # Arrange - Source missing Assert section
        mock_item = Mock()
        mock_item.name = "test_example"
        mock_getsource.return_value = """
def test_example():
    # Arrange - Set up test data and dependencies
    data = {"key": "value"}

    # Act - Execute the function under test
    result = process_data(data)
"""

        # Act - Validate AAA structure
        config = DrillSergeantConfig()
        issues = _validate_aaa_structure(mock_item, config)

        # Assert - Has issue for missing Assert
        assert_issues = [i for i in issues if "missing 'Assert'" in i.message]
        assert len(assert_issues) == 1
        assert assert_issues[0].issue_type == "aaa"

    @patch("pytest_drill_sergeant.validators.aaa.inspect.getsource")
    def test_validate_aaa_with_non_descriptive_comments(
        self, mock_getsource: Mock
    ) -> None:
        """# Arrange - Mock function source with non-descriptive AAA comments
        # Act - Validate AAA structure
        # Assert - Returns issues for non-descriptive comments
        """
        # Arrange - Source with non-descriptive comments
        mock_item = Mock()
        mock_item.name = "test_example"
        mock_getsource.return_value = """
def test_example():
    # Arrange
    data = {"key": "value"}

    # Act
    result = process_data(data)

    # Assert
    assert result == expected_value
"""

        # Act - Validate AAA structure
        config = DrillSergeantConfig()
        issues = _validate_aaa_structure(mock_item, config)

        # Assert - Has issues for missing sections (since comments don't follow proper format)
        assert len(issues) == 3
        for issue in issues:
            assert issue.issue_type == "aaa"
            assert "missing" in issue.message and "section" in issue.message

    @patch("pytest_drill_sergeant.validators.aaa.inspect.getsource")
    def test_validate_aaa_handles_os_error(self, mock_getsource: Mock) -> None:
        """# Arrange - Mock function that raises OSError when getting source
        # Act - Validate AAA structure
        # Assert - Returns no issues when OSError occurs
        """
        # Arrange - Mock that raises OSError
        mock_item = Mock()
        mock_item.name = "test_example"
        mock_getsource.side_effect = OSError("Cannot get source")

        # Act - Validate AAA structure
        config = DrillSergeantConfig()
        issues = _validate_aaa_structure(mock_item, config)

        # Assert - No issues when OSError occurs
        assert issues == []


@pytest.mark.unit
class TestReportAllIssues:
    """Test comprehensive issue reporting."""

    def test_report_all_issues_with_marker_and_aaa_issues(self) -> None:
        """# Arrange - Mock pytest item and mixed validation issues
        # Act - Report all issues
        # Assert - Pytest.fail is called with comprehensive error message
        """
        # Arrange - Mock item and mixed validation issues
        mock_item = Mock()
        mock_item.name = "test_example"

        issues = [
            ValidationIssue(
                issue_type="marker",
                message="Missing marker",
                suggestion="Add @pytest.mark.unit",
            ),
            ValidationIssue(
                issue_type="aaa",
                message="Missing Arrange",
                suggestion="Add '# Arrange - description'",
            ),
            ValidationIssue(
                issue_type="aaa",
                message="Missing Act",
                suggestion="Add '# Act - description'",
            ),
        ]

        # Act - Call _report_all_issues and capture the pytest.fail exception
        with pytest.raises(Failed) as exc_info:
            _report_all_issues(mock_item, issues)

        # Assert - Verify comprehensive error message content
        error_message = str(exc_info.value)
        assert "test_example" in error_message
        assert "missing test annotations and missing AAA structure" in error_message
        assert "🏷️  MISSING TEST CLASSIFICATION:" in error_message
        assert "📝 MISSING AAA STRUCTURE" in error_message
        assert "PROJECT REQUIREMENT" in error_message

    def test_report_all_issues_with_only_marker_issues(self) -> None:
        """# Arrange - Mock pytest item and only marker validation issues
        # Act - Report all issues
        # Assert - Pytest.fail is called with marker-specific error message
        """
        # Arrange - Mock item and marker validation issues only
        mock_item = Mock()
        mock_item.name = "test_example"

        issues = [
            ValidationIssue(
                issue_type="marker",
                message="Missing marker",
                suggestion="Add @pytest.mark.unit",
            ),
        ]

        # Act - Call _report_all_issues and capture the pytest.fail exception
        with pytest.raises(Failed) as exc_info:
            _report_all_issues(mock_item, issues)

        # Assert - Verify marker-specific error message content
        error_message = str(exc_info.value)
        assert "missing test annotations" in error_message
        assert "missing AAA structure" not in error_message
        assert "🏷️  MISSING TEST CLASSIFICATION:" in error_message
        assert "📝 MISSING AAA STRUCTURE" not in error_message

    def test_report_all_issues_with_only_aaa_issues(self) -> None:
        """# Arrange - Mock pytest item and only AAA validation issues
        # Act - Report all issues
        # Assert - Pytest.fail is called with AAA-specific error message
        """
        # Arrange - Mock item and AAA validation issues only
        mock_item = Mock()
        mock_item.name = "test_example"

        issues = [
            ValidationIssue(
                issue_type="aaa",
                message="Missing Arrange",
                suggestion="Add '# Arrange - description'",
            ),
        ]

        # Act - Call _report_all_issues and capture the pytest.fail exception
        with pytest.raises(Failed) as exc_info:
            _report_all_issues(mock_item, issues)

        # Assert - Verify AAA-specific error message content
        error_message = str(exc_info.value)
        assert "missing AAA structure" in error_message
        assert "missing test annotations" not in error_message
        assert "📝 MISSING AAA STRUCTURE" in error_message
        assert "🏷️  MISSING TEST CLASSIFICATION:" not in error_message


@pytest.mark.unit
class TestAAASynonymRecognition:
    """Test AAA synonym recognition functionality."""

    def test_build_aaa_keyword_lists_disabled_by_default(self) -> None:
        """# Arrange - Default configuration with synonyms disabled
        # Act - Build AAA keyword lists
        # Assert - Only original keywords are present
        """
        # Arrange - Default configuration with synonyms disabled
        config = DrillSergeantConfig()

        # Act - Build AAA keyword lists
        keywords = _build_aaa_keyword_lists(config)

        # Assert - Only original keywords should be present
        assert keywords["arrange"] == ["Arrange"]
        assert keywords["act"] == ["Act"]
        assert keywords["assert"] == ["Assert"]

    def test_build_aaa_keyword_lists_with_builtin_synonyms(self) -> None:
        """# Arrange - Configuration with built-in synonyms enabled
        # Act - Build AAA keyword lists
        # Assert - Original and built-in synonyms are included
        """
        # Arrange - Configuration with built-in synonyms enabled
        config = DrillSergeantConfig(
            aaa_synonyms_enabled=True, aaa_builtin_synonyms=True
        )

        # Act - Build AAA keyword lists
        keywords = _build_aaa_keyword_lists(config)

        # Assert - Should include original + built-in synonyms
        assert "Arrange" in keywords["arrange"]
        assert "Setup" in keywords["arrange"]
        assert "Given" in keywords["arrange"]

        assert "Act" in keywords["act"]
        assert "Call" in keywords["act"]
        assert "When" in keywords["act"]

        assert "Assert" in keywords["assert"]
        assert "Verify" in keywords["assert"]
        assert "Then" in keywords["assert"]

    def test_build_aaa_keyword_lists_with_custom_synonyms(self) -> None:
        """# Arrange - Configuration with custom synonyms and built-ins disabled
        # Act - Build AAA keyword lists
        # Assert - Only original and custom synonyms are included
        """
        # Arrange - Configuration with custom synonyms and built-ins disabled
        config = DrillSergeantConfig(
            aaa_synonyms_enabled=True,
            aaa_builtin_synonyms=False,  # Disable built-ins
            aaa_arrange_synonyms=["Background", "Precondition"],
            aaa_act_synonyms=["Execute", "Trigger"],
            aaa_assert_synonyms=["Expect", "Outcome"],
        )

        # Act - Build AAA keyword lists
        keywords = _build_aaa_keyword_lists(config)

        # Assert - Should include original + custom only (no built-ins)
        assert keywords["arrange"] == ["Arrange", "Background", "Precondition"]
        assert keywords["act"] == ["Act", "Execute", "Trigger"]
        assert keywords["assert"] == ["Assert", "Expect", "Outcome"]

    def test_build_aaa_keyword_lists_with_builtin_and_custom(self) -> None:
        """# Arrange - Configuration with both built-in and custom synonyms
        # Act - Build AAA keyword lists
        # Assert - All synonyms are included together
        """
        # Arrange - Configuration with both built-in and custom synonyms
        config = DrillSergeantConfig(
            aaa_synonyms_enabled=True,
            aaa_builtin_synonyms=True,
            aaa_arrange_synonyms=["Background"],
            aaa_act_synonyms=["Execute"],
            aaa_assert_synonyms=["Expect"],
        )

        # Act - Build AAA keyword lists
        keywords = _build_aaa_keyword_lists(config)

        # Assert - Should include original + built-ins + custom
        assert "Arrange" in keywords["arrange"]
        assert "Setup" in keywords["arrange"]  # Built-in
        assert "Background" in keywords["arrange"]  # Custom

        assert "Act" in keywords["act"]
        assert "Call" in keywords["act"]  # Built-in
        assert "Execute" in keywords["act"]  # Custom

    def test_synonym_detection_in_comments(self) -> None:
        """# Arrange - Configuration with synonyms enabled and validator
        # Act - Check AAA sections with built-in synonyms
        # Assert - Synonyms are properly detected
        """
        # Arrange - Configuration with synonyms enabled and validator
        config = DrillSergeantConfig(aaa_synonyms_enabled=True)
        validator = AAAValidator()

        # Act - Test built-in synonyms
        status = validator._check_aaa_sections(
            ["# Setup - test data"], "test_func", config
        )

        # Assert - Synonyms are properly detected
        assert status.arrange_found is True

        status = validator._check_aaa_sections(
            ["# Call - the authentication method"], "test_func", config
        )
        assert status.act_found is True

        status = validator._check_aaa_sections(
            ["# Verify - the result is correct"], "test_func", config
        )
        assert status.assert_found is True

    def test_custom_synonym_detection(self) -> None:
        """# Arrange - Configuration with custom BDD-style synonyms
        # Act - Check AAA sections with custom synonyms
        # Assert - Custom synonyms are properly detected
        """
        # Arrange - Configuration with custom BDD-style synonyms
        config = DrillSergeantConfig(
            aaa_synonyms_enabled=True,
            aaa_builtin_synonyms=False,
            aaa_arrange_synonyms=["Given"],
            aaa_act_synonyms=["When"],
            aaa_assert_synonyms=["Then"],
        )
        validator = AAAValidator()

        # Act - Test BDD-style synonyms
        status = validator._check_aaa_sections(
            ["# Given - a valid user account"], "test_func", config
        )

        # Assert - Custom synonyms are properly detected
        assert status.arrange_found is True

        status = validator._check_aaa_sections(
            ["# When - logging in with credentials"], "test_func", config
        )
        assert status.act_found is True

        status = validator._check_aaa_sections(
            ["# Then - authentication should succeed"], "test_func", config
        )
        assert status.assert_found is True

    def test_synonym_disabled_detection(self) -> None:
        """# Arrange - Configuration with synonyms disabled
        # Act - Check AAA sections with synonym keywords
        # Assert - Synonyms are not detected but original keywords work
        """
        # Arrange - Configuration with synonyms disabled
        config = DrillSergeantConfig(aaa_synonyms_enabled=False)
        validator = AAAValidator()

        # Act - These should NOT be detected when synonyms are disabled
        status = validator._check_aaa_sections(
            ["# Setup - test data"], "test_func", config
        )

        # Assert - Synonyms are not detected but original keywords work
        assert status.arrange_found is False

        status = validator._check_aaa_sections(
            ["# Call - the method"], "test_func", config
        )
        assert status.act_found is False

        status = validator._check_aaa_sections(
            ["# Verify - the result"], "test_func", config
        )
        assert status.assert_found is False

        # But original keywords should still work
        status = validator._check_aaa_sections(
            ["# Arrange - test data"], "test_func", config
        )
        assert status.arrange_found is True
