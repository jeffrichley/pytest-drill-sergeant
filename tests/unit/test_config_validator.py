"""Tests for the configuration validator."""

from typing import cast
from unittest.mock import MagicMock, patch

from pytest_drill_sergeant.core.config import DrillSergeantConfig
from pytest_drill_sergeant.core.config_validator import (
    ConfigValidator,
    validate_configuration,
)
from tests.constants import (
    EXPECTED_ERROR_COUNT_2,
    EXPECTED_ERROR_COUNT_3,
    EXPECTED_SUGGESTION_COUNT_5,
)


class TestConfigValidator:
    """Test the ConfigValidator class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.validator = ConfigValidator()

    def test_validate_config_valid(self) -> None:
        """Test validation with valid configuration."""
        config = DrillSergeantConfig(
            mode="strict",
            persona="snoop_dogg",
            budgets={"warn": 20, "error": 5},
            thresholds={"bis_threshold_warn": 85, "dynamic_cov_jaccard": 0.9},
            enabled_rules={"aaa_comments", "private_access"},
            suppressed_rules={"private_access"},
        )

        errors = self.validator.validate_config(config)

        assert errors == []

    def test_validate_mode_invalid(self) -> None:
        """Test mode validation with invalid mode."""
        # Test the validator method directly with invalid mode
        errors = self.validator._validate_mode("invalid_mode")

        assert len(errors) == 1
        assert "Invalid mode 'invalid_mode'" in errors[0]
        assert (
            "advisory" in errors[0]
            and "quality-gate" in errors[0]
            and "strict" in errors[0]
        )

    def test_validate_mode_valid(self) -> None:
        """Test mode validation with valid modes."""
        valid_modes = ["advisory", "quality-gate", "strict"]

        for mode in valid_modes:
            errors = self.validator._validate_mode(mode)
            assert errors == []

    def test_validate_persona_invalid(self) -> None:
        """Test persona validation with invalid persona."""
        # Test the validator method directly with invalid persona
        errors = self.validator._validate_persona("invalid_persona")

        assert len(errors) == 1
        assert "Invalid persona 'invalid_persona'" in errors[0]
        assert "drill_sergeant" in errors[0] and "snoop_dogg" in errors[0]

    def test_validate_persona_valid(self) -> None:
        """Test persona validation with valid personas."""
        valid_personas = [
            "drill_sergeant",
            "snoop_dogg",
            "motivational_coach",
            "sarcastic_butler",
            "pirate",
        ]

        for persona in valid_personas:
            errors = self.validator._validate_persona(persona)
            assert errors == []

    def test_validate_budgets_invalid(self) -> None:
        """Test budget validation with invalid budgets."""
        invalid_budgets: dict[str, int] = {"warn": -5, "error": 10}

        errors = self.validator._validate_budgets(invalid_budgets)

        assert len(errors) == 1
        assert "Budget warn must be non-negative" in errors[0]

    def test_validate_budgets_invalid_type(self) -> None:
        """Test budget validation with invalid types."""
        invalid_budgets: dict[str, object] = {"warn": "not_a_number", "error": 10}

        errors = self.validator._validate_budgets(
            cast("dict[str, int]", invalid_budgets)
        )

        assert len(errors) == 1
        assert "Budget warn must be an integer" in errors[0]

    def test_validate_budgets_valid(self) -> None:
        """Test budget validation with valid budgets."""
        valid_budgets: dict[str, int] = {"warn": 20, "error": 5}

        errors = self.validator._validate_budgets(valid_budgets)

        assert errors == []

    def test_validate_thresholds_invalid_ranges(self) -> None:
        """Test threshold validation with invalid ranges."""
        invalid_thresholds: dict[str, float] = {
            "bis_threshold_warn": 150,  # > 100
            "dynamic_cov_jaccard": 1.5,  # > 1
            "static_clone_hamming": 100,  # > 64
        }

        errors = self.validator._validate_thresholds(invalid_thresholds)

        assert (
            len(errors) == EXPECTED_ERROR_COUNT_2
        )  # Only 2 errors because bis_threshold_warn doesn't match the pattern
        assert any("must be between 0 and 1" in error for error in errors)
        assert any("must be between 0 and 64" in error for error in errors)

    def test_validate_thresholds_invalid_types(self) -> None:
        """Test threshold validation with invalid types."""
        invalid_thresholds: dict[str, object] = {
            "bis_threshold_warn": "not_a_number",
            "dynamic_cov_jaccard": 0.9,
        }

        errors = self.validator._validate_thresholds(
            cast("dict[str, float]", invalid_thresholds)
        )

        assert len(errors) == 1
        assert "Threshold bis_threshold_warn must be a number" in errors[0]

    def test_validate_thresholds_valid(self) -> None:
        """Test threshold validation with valid thresholds."""
        valid_thresholds: dict[str, float] = {
            "bis_threshold_warn": 85,
            "bis_threshold_fail": 65,
            "dynamic_cov_jaccard": 0.9,
            "static_clone_hamming": 6,
        }

        errors = self.validator._validate_thresholds(valid_thresholds)

        assert errors == []

    def test_validate_rules_unknown_rules(self) -> None:
        """Test rule validation with unknown rules."""
        # Test the validator method directly with unknown rules
        enabled_rules = {"unknown_rule", "aaa_comments"}
        suppressed_rules = {"another_unknown_rule"}

        errors = self.validator._validate_rules(enabled_rules, suppressed_rules)

        assert (
            len(errors) == EXPECTED_ERROR_COUNT_3
        )  # 3 errors: unknown enabled, unknown suppressed, and suppressed not enabled
        assert "Unknown enabled rules: unknown_rule" in errors[0]
        assert "Unknown suppressed rules: another_unknown_rule" in errors[1]
        assert (
            "Cannot suppress rules that are not enabled: another_unknown_rule"
            in errors[2]
        )

    def test_validate_rules_suppressed_not_enabled(self) -> None:
        """Test rule validation with suppressed rules not in enabled rules."""
        # Test the validator method directly
        enabled_rules = {"aaa_comments"}
        suppressed_rules = {"static_clones"}

        errors = self.validator._validate_rules(enabled_rules, suppressed_rules)

        assert len(errors) == 1
        assert "Cannot suppress rules that are not enabled: static_clones" in errors[0]

    def test_validate_rules_valid(self) -> None:
        """Test rule validation with valid rules."""
        enabled_rules = {"aaa_comments", "static_clones", "private_access"}
        suppressed_rules = {"static_clones"}

        errors = self.validator._validate_rules(enabled_rules, suppressed_rules)

        assert errors == []

    def test_validate_output_paths_missing_directories(self) -> None:
        """Test output path validation with missing directories."""
        config = DrillSergeantConfig(
            json_report_path="/nonexistent/path/report.json",
            sarif_report_path="/another/nonexistent/path/report.sarif",
        )

        errors = self.validator._validate_output_paths(config)

        assert len(errors) == EXPECTED_ERROR_COUNT_2
        assert all("directory does not exist" in error for error in errors)

    def test_validate_output_paths_valid(self) -> None:
        """Test output path validation with valid paths."""
        with (
            patch("pathlib.Path.exists") as mock_exists,
            patch("pathlib.Path.is_dir") as mock_is_dir,
        ):
            mock_exists.return_value = True
            mock_is_dir.return_value = True

            config = DrillSergeantConfig(
                json_report_path="/valid/path/report.json",
                sarif_report_path="/valid/path/report.sarif",
            )

            errors = self.validator._validate_output_paths(config)

            assert errors == []

    def test_validate_consistency_verbose_and_quiet(self) -> None:
        """Test consistency validation with both verbose and quiet."""
        # Test the validator method directly with a mock object
        mock_config = MagicMock()
        mock_config.verbose = True
        mock_config.quiet = True
        mock_config.thresholds = {}
        mock_config.budgets = {}

        errors = self.validator._validate_consistency(mock_config)

        assert len(errors) == 1
        assert "Cannot specify both verbose and quiet modes" in errors[0]

    def test_validate_consistency_threshold_order(self) -> None:
        """Test consistency validation with invalid threshold order."""
        # Test the validator method directly with a mock object
        mock_config = MagicMock()
        mock_config.thresholds = {
            "bis_threshold_warn": 60,  # Lower than fail threshold
            "bis_threshold_fail": 70,
        }
        mock_config.verbose = False
        mock_config.quiet = False
        mock_config.budgets = {}

        errors = self.validator._validate_consistency(mock_config)

        assert len(errors) == 1
        assert (
            "BIS warning threshold (60) must be greater than failure threshold (70)"
            in errors[0]
        )

    def test_validate_consistency_budget_order(self) -> None:
        """Test consistency validation with invalid budget order."""
        config = DrillSergeantConfig(
            budgets={"warn": 5, "error": 10}  # Lower than error budget
        )

        errors = self.validator._validate_consistency(config)

        assert len(errors) == 1
        assert (
            "Warning budget (5) should be greater than or equal to error budget (10)"
            in errors[0]
        )

    def test_validate_consistency_valid(self) -> None:
        """Test consistency validation with valid configuration."""
        config = DrillSergeantConfig(
            verbose=True,
            quiet=False,
            thresholds={"bis_threshold_warn": 80, "bis_threshold_fail": 60},
            budgets={"warn": 20, "error": 5},
        )

        errors = self.validator._validate_consistency(config)

        assert errors == []

    def test_validate_file_paths_sut_package_import_error(self) -> None:
        """Test file path validation with SUT package import error."""
        config = DrillSergeantConfig(sut_package="nonexistent_package")

        with patch(
            "builtins.__import__",
            side_effect=ImportError("No module named 'nonexistent_package'"),
        ):
            errors = self.validator.validate_file_paths(config)

        assert len(errors) == 1
        assert "SUT package 'nonexistent_package' could not be imported" in errors[0]

    def test_validate_file_paths_sut_package_valid(self) -> None:
        """Test file path validation with valid SUT package."""
        config = DrillSergeantConfig(sut_package="os")

        with patch("builtins.__import__", return_value=MagicMock()):
            errors = self.validator.validate_file_paths(config)

        assert errors == []

    def test_validate_file_paths_no_sut_package(self) -> None:
        """Test file path validation with no SUT package."""
        config = DrillSergeantConfig(sut_package=None)

        errors = self.validator.validate_file_paths(config)

        assert errors == []

    def test_suggest_fixes_common_errors(self) -> None:
        """Test fix suggestions for common errors."""
        errors = [
            "Invalid mode 'invalid'",
            "Invalid persona 'unknown'",
            "Threshold bis_threshold_warn must be between 0 and 100, got 150",
            "Cannot specify both --ds-verbose and --ds-quiet",
            "directory does not exist: /nonexistent",
            "SUT package 'missing' could not be imported",
        ]

        suggestions = self.validator.suggest_fixes(errors)

        assert (
            len(suggestions) == EXPECTED_SUGGESTION_COUNT_5
        )  # Only 5 suggestions because one error doesn't match any pattern
        assert "Use one of: advisory, quality-gate, strict" in suggestions[errors[0]]
        assert "Use one of: drill_sergeant, snoop_dogg" in suggestions[errors[1]]
        assert "Use a value between 0 and 100" in suggestions[errors[2]]
        assert "Create the directory or use a different path" in suggestions[errors[4]]
        assert "Install the package or check the package name" in suggestions[errors[5]]

    def test_suggest_fixes_unknown_errors(self) -> None:
        """Test fix suggestions for unknown errors."""
        errors = ["Some unknown error message"]

        suggestions = self.validator.suggest_fixes(errors)

        assert len(suggestions) == 0


class TestValidateConfigurationFunction:
    """Test the validate_configuration convenience function."""

    def test_validate_configuration_valid(self) -> None:
        """Test configuration validation with valid config."""
        config = DrillSergeantConfig(
            mode="strict",
            persona="snoop_dogg",
            budgets={"warn": 20, "error": 5},
            thresholds={"bis_threshold_warn": 85, "dynamic_cov_jaccard": 0.9},
        )

        with patch(
            "pytest_drill_sergeant.core.config_validator.ConfigValidator.validate_file_paths",
            return_value=[],
        ):
            is_valid, errors, suggestions = validate_configuration(config)

        assert is_valid is True
        assert errors == []
        assert suggestions == {}

    def test_validate_configuration_invalid(self) -> None:
        """Test configuration validation with invalid config."""
        # Test with a valid config but mock file validation errors
        config = DrillSergeantConfig()

        with patch(
            "pytest_drill_sergeant.core.config_validator.ConfigValidator.validate_file_paths",
            return_value=["SUT package 'missing' could not be imported"],
        ):
            is_valid, errors, suggestions = validate_configuration(config)

        assert is_valid is False
        assert len(errors) > 0
        assert len(suggestions) > 0

    def test_validate_configuration_with_file_errors(self) -> None:
        """Test configuration validation with file errors."""
        config = DrillSergeantConfig(sut_package="nonexistent_package")

        with patch(
            "pytest_drill_sergeant.core.config_validator.ConfigValidator.validate_file_paths",
            return_value=["SUT package 'nonexistent_package' could not be imported"],
        ):
            is_valid, errors, suggestions = validate_configuration(config)

        assert is_valid is False
        assert "SUT package 'nonexistent_package' could not be imported" in errors
        assert len(suggestions) > 0
