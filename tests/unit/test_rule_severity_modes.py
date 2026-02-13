"""Unit tests for rule severity behavior (error/warn/off)."""

from unittest.mock import Mock, patch

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.validators.aaa import AAAValidator
from pytest_drill_sergeant.validators.marker import MarkerValidator


@pytest.mark.unit
class TestRuleSeverityModes:
    """Validate marker and AAA severity handling."""

    def test_marker_warn_mode_emits_warning_and_returns_no_issues(self) -> None:
        """Warn mode should not block execution for marker violations."""
        # Arrange - Markerless item and warn severity config
        item = Mock()
        item.name = "test_missing_marker"
        item.iter_markers.return_value = []
        item.config = Mock()

        config = DrillSergeantConfig(
            auto_detect_markers=False,
            marker_severity="warn",
            enforce_markers=True,
        )

        # Act - Validate marker rule in warn mode
        # Assert - Warn mode emits warnings and does not block
        with pytest.warns(pytest.PytestWarning):
            issues = MarkerValidator().validate(item, config)

        # Assert - Marker warn mode does not return blocking issues
        assert issues == []

    def test_marker_off_mode_disables_validator(self) -> None:
        """Off mode should disable marker validator entirely."""
        # Arrange - Marker rule configured off
        config = DrillSergeantConfig(marker_severity="off", enforce_markers=True)

        # Act - Check marker validator enablement
        # Assert - Validator is disabled in off mode
        assert MarkerValidator().is_enabled(config) is False

    @patch("pytest_drill_sergeant.validators.aaa.inspect.getsource")
    def test_aaa_warn_mode_emits_warning_and_returns_no_issues(
        self, mock_getsource: Mock
    ) -> None:
        """Warn mode should emit warnings instead of issues for AAA violations."""
        # Arrange - Source without AAA comments and warn severity config
        mock_getsource.return_value = (
            "def test_missing_aaa() -> None:\n"
            "    value = 1\n"
            "    assert value == 1\n"
        )

        def sample_test() -> None:
            return None

        item = Mock()
        item.name = "test_missing_aaa"
        item.function = sample_test

        config = DrillSergeantConfig(aaa_severity="warn", enforce_aaa=True)

        # Act - Validate AAA rule in warn mode
        # Assert - Warn mode emits warnings and does not block
        with pytest.warns(pytest.PytestWarning):
            issues = AAAValidator().validate(item, config)

        # Assert - AAA warn mode does not return blocking issues
        assert issues == []

    def test_aaa_off_mode_disables_validator(self) -> None:
        """Off mode should disable AAA validator entirely."""
        # Arrange - AAA rule configured off
        config = DrillSergeantConfig(aaa_severity="off", enforce_aaa=True)

        # Act - Check AAA validator enablement
        # Assert - Validator is disabled in off mode
        assert AAAValidator().is_enabled(config) is False
